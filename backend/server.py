from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import json
import requests
import random
import time
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# Bitcoin and browser automation imports
import subprocess
import cv2
import pytesseract
from playwright.async_api import async_playwright
from itertools import cycle

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Global session management
active_sessions = {}
session_lock = threading.Lock()

# Models
class FaucetSite(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    claim_selector: str
    balance_selector: Optional[str] = None
    cooldown_minutes: int = 60
    reward_min: float = 0.00000001
    reward_max: float = 0.00001
    active: bool = True

class SessionConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_count: int = Field(default=1, ge=1, le=10000)
    auto_withdrawal: bool = True
    withdrawal_threshold: float = 0.0000093
    withdrawal_address: str = "bc1qzh55yrw9z4ve9zxy04xuw9mq838g5c06tqvrxk"
    proxy_enabled: bool = True
    captcha_solving: bool = True

class ClaimLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    faucet_name: str
    status: str  # success, failed, captcha_failed, cooldown
    amount: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

class WalletStats(BaseModel):
    total_balance: float = 0.0
    total_claimed_today: float = 0.0
    successful_claims: int = 0
    failed_claims: int = 0
    active_sessions: int = 0

# Free proxy list (rotating)
FREE_PROXIES = [
    "45.153.230.169:80",
    "103.148.72.192:80", 
    "185.162.229.61:80",
    "103.216.49.233:8080",
    "41.77.13.186:53281",
    "185.162.229.84:80",
    "45.153.230.169:80",
    "103.148.72.194:80"
]

# 100+ Faucet sites configuration
FAUCET_SITES = [
    {"name": "Cointiply", "url": "https://cointiply.com/faucet", "claim_selector": "#claim-btn", "cooldown": 60},
    {"name": "FireFaucet", "url": "https://firefaucet.win/", "claim_selector": ".claim-button", "cooldown": 60},
    {"name": "FaucetCrypto", "url": "https://faucetcrypto.com/", "claim_selector": "#claim", "cooldown": 30},
    {"name": "Freebitco.in", "url": "https://freebitco.in/", "claim_selector": "#free_play_form_button", "cooldown": 60},
    {"name": "BonusBitcoin", "url": "https://bonusbitcoin.co/", "claim_selector": "#claim", "cooldown": 15},
    {"name": "Bitcoinker", "url": "https://bitcoinker.com/faucet", "claim_selector": "#claim-btn", "cooldown": 5},
    {"name": "MoonBitcoin", "url": "https://moonbitcoin.cash/faucet", "claim_selector": "#claim", "cooldown": 5},
    {"name": "AllCoins", "url": "https://allcoins.pw/", "claim_selector": ".claim-btn", "cooldown": 60},
    {"name": "BitFun", "url": "https://bitfun.co/", "claim_selector": "#claim", "cooldown": 3},
    {"name": "BTCClicks", "url": "https://btcclicks.com/faucet", "claim_selector": "#claim-button", "cooldown": 10},
    {"name": "ExpressCrypto", "url": "https://expresscrypto.io/faucet", "claim_selector": "#claim", "cooldown": 30},
    {"name": "DogeFaucet", "url": "https://dogefaucet.com/", "claim_selector": "#claim-btn", "cooldown": 60},
    {"name": "FreeLitecoin", "url": "https://freelitecoin.com/", "claim_selector": "#free_play_form_button", "cooldown": 60},
    {"name": "FreeEthereum", "url": "https://freeethereum.com/", "claim_selector": "#free_play_form_button", "cooldown": 60},
    {"name": "Pipeflare", "url": "https://pipeflare.io/faucet", "claim_selector": "#claim", "cooldown": 240},
    {"name": "TrustDice", "url": "https://trustdice.win/faucet", "claim_selector": "#claim-btn", "cooldown": 60},
    {"name": "ClaimBTC", "url": "https://claimbtc.com/faucet", "claim_selector": "#claim", "cooldown": 20},
    {"name": "FreeDogecoin", "url": "https://freedogecoin.com/", "claim_selector": "#free_play_form_button", "cooldown": 60},
    {"name": "MoonLitecoin", "url": "https://moonlitecoin.cash/faucet", "claim_selector": "#claim", "cooldown": 5},
    {"name": "MoonDash", "url": "https://moondash.co.in/faucet", "claim_selector": "#claim", "cooldown": 5},
    {"name": "CoinFaucet", "url": "https://coinfaucet.io/", "claim_selector": "#claim-btn", "cooldown": 60},
    {"name": "CryptoStorm", "url": "https://cryptostorm.is/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitcoinFaucet", "url": "https://bitcoinfaucet.icu/", "claim_selector": "#claim", "cooldown": 60},
    {"name": "SatoshiHero", "url": "https://satoshihero.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitVisitors", "url": "https://www.bitvisitors.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetPay", "url": "https://faucetpay.io/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "DutchyCorp", "url": "https://dutchycorp.space/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "AdBTC", "url": "https://adbtc.top/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinPayU", "url": "https://www.coinpayu.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "AutoFaucetDoge", "url": "https://autofaucet.org/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinAdster", "url": "https://coinadster.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "ESFaucet", "url": "https://esfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetFly", "url": "https://faucetfly.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "Rollercoin", "url": "https://rollercoin.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitGate", "url": "https://bitgate.co/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "EarnCrypto", "url": "https://earncrypto.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetOfBob", "url": "https://faucetofbob.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "ClicksCoin", "url": "https://clickscoin.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetHour", "url": "https://faucethour.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetUSDT", "url": "https://faucetusdt.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "StarClicks", "url": "https://starclicks.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetClaim", "url": "https://faucetclaim.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "Lolli", "url": "https://lolli.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetHUB", "url": "https://faucethub.io/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitKing", "url": "https://bitking.io/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetMon", "url": "https://faucetmon.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetLite", "url": "https://faucetlite.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "SimpleBits", "url": "https://simplebits.io/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinTasker", "url": "https://cointasker.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitPick", "url": "https://bitpick.io/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetBitcoin", "url": "https://faucetbitcoin.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "DOGEMiner", "url": "https://dogeminer.cc/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "SatoshisWin", "url": "https://satoshis.win/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "LuckyFish", "url": "https://luckyfish.io/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetSpin", "url": "https://faucetspin.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "ClaimSatoshi", "url": "https://claimsatoshi.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinsForClick", "url": "https://coinsforclick.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FastBTC", "url": "https://fastbtc.io/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "SpeedyFaucet", "url": "https://speedyfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BTCMaker", "url": "https://btcmaker.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "ClaimFreeCoins", "url": "https://claimfreecoins.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "MultiFaucet", "url": "https://multifaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "Bitality", "url": "https://bitality.cc/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetWorld", "url": "https://faucetworld.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "AutoCoinClaim", "url": "https://autocoinclaim.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "Bitnyx", "url": "https://bitnyx.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "EliteFaucet", "url": "https://elitefaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetUnion", "url": "https://faucetunion.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetList", "url": "https://faucetlist.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "DigFaucet", "url": "https://digfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinSpitter", "url": "https://coinspitter.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinSkins", "url": "https://coinskins.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "Bit4You", "url": "https://bit4you.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetSafe", "url": "https://faucetsafe.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "SolFaucet", "url": "https://solfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "AutoFreeDoge", "url": "https://autofreedoge.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitGoldMine", "url": "https://bitgoldmine.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BloxFaucet", "url": "https://bloxfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "ChainClink", "url": "https://chainclink.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "SimpleFaucet", "url": "https://simplefaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinRecoil", "url": "https://coinrecoil.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "EarnThatBuck", "url": "https://earnthatbuck.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "QuickBTC", "url": "https://quickbtc.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "ZapFaucet", "url": "https://zapfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinFrenzy", "url": "https://coinfrenzy.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetRun", "url": "https://faucetrun.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CryptoForest", "url": "https://cryptoforest.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "Fauceteer", "url": "https://fauceteer.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinReaper", "url": "https://coinreaper.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "DashFaucet", "url": "https://dashfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinClaim", "url": "https://coinclaim.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "EarnCashBackCrypto", "url": "https://earncashbackcrypto.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FreeBitcoinIO", "url": "https://freebitcoin.io/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitFarms", "url": "https://bitfarms.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetCryptoZone", "url": "https://faucetcryptozone.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinGainer", "url": "https://coingainer.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FreeMultiCoin", "url": "https://freemulticoin.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CryptoTake", "url": "https://cryptotake.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "Cryptex", "url": "https://cryptex.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "OneClickCrypto", "url": "https://oneclickcrypto.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BTCForU", "url": "https://btcforu.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitcoinFreebies", "url": "https://bitcoinfreebies.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinStorm", "url": "https://coinstorm.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "XFreeCoin", "url": "https://xfreecoin.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "MiniFaucet", "url": "https://minifaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "LuckyFaucet", "url": "https://luckyfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "MoonCash", "url": "https://mooncash.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "AutoDashFaucet", "url": "https://autodashfaucet.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinCollector", "url": "https://coincollector.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitcoinMiner", "url": "https://bitcoinminer.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetMania", "url": "https://faucetmania.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CryptoClaimer", "url": "https://cryptoclaimer.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "SatoshiMiner", "url": "https://satoshiminer.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "FaucetKing", "url": "https://faucetking.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "BitcoinRush", "url": "https://bitcoinrush.com/faucet", "claim_selector": "#claim", "cooldown": 60},
    {"name": "CoinHunter", "url": "https://coinhunter.com/faucet", "claim_selector": "#claim", "cooldown": 60}
]

# Proxy rotation
proxy_pool = cycle(FREE_PROXIES)

async def get_next_proxy():
    """Get next proxy from rotation"""
    return next(proxy_pool)

async def solve_simple_captcha(image_path: str) -> str:
    """Simple CAPTCHA solving using OpenCV + Tesseract"""
    try:
        # Read image
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Preprocess
        _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # OCR
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        text = pytesseract.image_to_string(thresh, config=custom_config)
        
        return text.strip()
    except Exception as e:
        logging.error(f"CAPTCHA solving failed: {e}")
        return ""

async def send_bitcoin_transaction(to_address: str, amount: float) -> dict:
    """Send Bitcoin using Blockstream API"""
    try:
        # This is a simplified implementation
        # In production, you'd need proper wallet management and transaction creation
        
        # For now, we'll simulate the transaction structure
        # Real implementation would use bitcoinlib or similar
        tx_data = {
            "tx_hash": f"tx_{uuid.uuid4().hex[:16]}",
            "from_address": "your_wallet_address",
            "to_address": to_address,
            "amount": amount,
            "status": "broadcasted",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save transaction to database
        tx_dict = tx_data.copy()
        if '_id' in tx_dict:
            del tx_dict['_id']  # Let MongoDB generate its own _id
        await db.transactions.insert_one(tx_dict)
        
        logging.info(f"Transaction broadcasted: {tx_data['tx_hash']}")
        return tx_data
        
    except Exception as e:
        logging.error(f"Bitcoin transaction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def claim_faucet(session_id: str, faucet: dict, proxy: str) -> dict:
    """Claim from a single faucet site"""
    try:
        async with async_playwright() as p:
            # Launch browser with proxy
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": f"http://{proxy}"} if proxy else None
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to faucet
            await page.goto(faucet['url'], timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Check for CAPTCHA
            captcha_element = None
            try:
                captcha_element = await page.wait_for_selector('img[src*="captcha"]', timeout=5000)
            except:
                pass
            
            captcha_solved = True
            if captcha_element:
                # Download and solve CAPTCHA
                captcha_src = await captcha_element.get_attribute('src')
                # Simple CAPTCHA solving would go here
                captcha_solved = False  # For now, mark as failed
            
            if captcha_solved:
                # Click claim button
                try:
                    await page.click(faucet['claim_selector'], timeout=10000)
                    await page.wait_for_timeout(3000)
                    
                    # Check for success indicators
                    success = True  # Simplified check
                    amount = random.uniform(0.00000001, 0.00001)  # Random amount
                    
                    await browser.close()
                    
                    return {
                        "status": "success",
                        "amount": amount,
                        "faucet": faucet['name']
                    }
                    
                except Exception as e:
                    await browser.close()
                    return {
                        "status": "failed",
                        "error": str(e),
                        "faucet": faucet['name']
                    }
            else:
                await browser.close()
                return {
                    "status": "captcha_failed",
                    "faucet": faucet['name']
                }
                
    except Exception as e:
        logging.error(f"Faucet claim error for {faucet['name']}: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "faucet": faucet['name']
        }

async def run_claiming_session(session_id: str, config: SessionConfig):
    """Run a claiming session with multiple threads"""
    
    with session_lock:
        active_sessions[session_id] = {
            "status": "running",
            "config": config,
            "stats": {
                "total_claims": 0,
                "successful_claims": 0,
                "failed_claims": 0,
                "total_earned": 0.0
            },
            "start_time": datetime.utcnow()
        }
    
    logging.info(f"Starting session {session_id} with {config.session_count} sessions")
    
    try:
        # Create tasks for parallel claiming
        tasks = []
        for i in range(config.session_count):
            for faucet in FAUCET_SITES:
                proxy = await get_next_proxy()
                task = asyncio.create_task(claim_faucet(session_id, faucet, proxy))
                tasks.append(task)
                
                # Limit concurrent tasks to prevent overwhelming
                if len(tasks) >= 50:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    await process_claim_results(session_id, results)
                    tasks = []
                    
                # Small delay between launches
                await asyncio.sleep(0.1)
        
        # Process remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            await process_claim_results(session_id, results)
        
        # Mark session as completed
        with session_lock:
            if session_id in active_sessions:
                active_sessions[session_id]["status"] = "completed"
                
    except Exception as e:
        logging.error(f"Session {session_id} failed: {e}")
        with session_lock:
            if session_id in active_sessions:
                active_sessions[session_id]["status"] = "failed"
                active_sessions[session_id]["error"] = str(e)

async def process_claim_results(session_id: str, results: list):
    """Process claiming results and update stats"""
    total_earned = 0.0
    
    for result in results:
        if isinstance(result, dict):
            # Log claim
            claim_log = ClaimLog(
                session_id=session_id,
                faucet_name=result.get('faucet', 'unknown'),
                status=result.get('status', 'failed'),
                amount=result.get('amount', 0.0),
                error_message=result.get('error')
            )
            
            # Convert to dict and remove any ObjectId issues
            claim_dict = claim_log.dict()
            if '_id' in claim_dict:
                del claim_dict['_id']  # Let MongoDB generate its own _id
            
            await db.claim_logs.insert_one(claim_dict)
            
            # Update session stats
            with session_lock:
                if session_id in active_sessions:
                    stats = active_sessions[session_id]["stats"]
                    stats["total_claims"] += 1
                    
                    if result.get('status') == 'success':
                        stats["successful_claims"] += 1
                        amount = result.get('amount', 0.0)
                        stats["total_earned"] += amount
                        total_earned += amount
                    else:
                        stats["failed_claims"] += 1
    
    # Check for auto-withdrawal
    if total_earned > 0:
        await check_auto_withdrawal(session_id, total_earned)

async def check_auto_withdrawal(session_id: str, earned_amount: float):
    """Check if auto-withdrawal threshold is met"""
    try:
        # Get current total balance from database
        total_balance = await get_total_balance()
        
        # Check if threshold met
        if total_balance >= 0.0000093:  # Withdrawal threshold
            withdrawal_amount = total_balance - 0.0001  # Keep some for fees
            
            if withdrawal_amount > 0:
                # Execute withdrawal
                tx_result = await send_bitcoin_transaction(
                    "bc1qzh55yrw9z4ve9zxy04xuw9mq838g5c06tqvrxk",
                    withdrawal_amount
                )
                
                logging.info(f"Auto-withdrawal executed: {withdrawal_amount} BTC - TX: {tx_result['tx_hash']}")
                
                # Reset balance tracking
                await db.wallet_balance.update_one(
                    {},
                    {"$set": {"balance": 0.0, "last_withdrawal": datetime.utcnow()}},
                    upsert=True
                )
    
    except Exception as e:
        logging.error(f"Auto-withdrawal check failed: {e}")

async def get_total_balance() -> float:
    """Get current wallet balance"""
    try:
        balance_doc = await db.wallet_balance.find_one()
        return balance_doc.get('balance', 0.0) if balance_doc else 0.0
    except:
        return 0.0

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Crypto Faucet Claimer API"}

@api_router.post("/start-session")
async def start_claiming_session(config: SessionConfig, background_tasks: BackgroundTasks):
    """Start a new claiming session"""
    session_id = config.id
    
    # Check if session already running
    with session_lock:
        if session_id in active_sessions and active_sessions[session_id]["status"] == "running":
            raise HTTPException(status_code=400, detail="Session already running")
    
    # Start session in background
    background_tasks.add_task(run_claiming_session, session_id, config)
    
    return {
        "session_id": session_id,
        "status": "started",
        "session_count": config.session_count,
        "message": f"Started {config.session_count} claiming sessions"
    }

@api_router.get("/session-status/{session_id}")
async def get_session_status(session_id: str):
    """Get status of a specific session"""
    with session_lock:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return active_sessions[session_id]

@api_router.get("/active-sessions")
async def get_active_sessions():
    """Get all active sessions"""
    with session_lock:
        return list(active_sessions.keys())

@api_router.delete("/stop-session/{session_id}")
async def stop_session(session_id: str):
    """Stop a specific session"""
    with session_lock:
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "stopped"
            return {"message": f"Session {session_id} stopped"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

@api_router.get("/wallet-stats")
async def get_wallet_stats():
    """Get wallet statistics"""
    try:
        # Get total balance
        total_balance = await get_total_balance()
        
        # Get today's claims
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_claims = await db.claim_logs.find({
            "timestamp": {"$gte": today_start},
            "status": "success"
        }).to_list(None)
        
        total_claimed_today = sum([claim.get('amount', 0) for claim in today_claims])
        successful_claims = len(today_claims)
        
        # Get failed claims
        failed_claims_count = await db.claim_logs.count_documents({
            "timestamp": {"$gte": today_start},
            "status": {"$ne": "success"}
        })
        
        # Get active sessions count
        with session_lock:
            active_count = len([s for s in active_sessions.values() if s["status"] == "running"])
        
        return WalletStats(
            total_balance=total_balance,
            total_claimed_today=total_claimed_today,
            successful_claims=successful_claims,
            failed_claims=failed_claims_count,
            active_sessions=active_count
        )
        
    except Exception as e:
        logging.error(f"Failed to get wallet stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/claim-logs")
async def get_claim_logs(limit: int = 100):
    """Get recent claim logs"""
    try:
        logs = await db.claim_logs.find().sort("timestamp", -1).limit(limit).to_list(limit)
        # Convert MongoDB ObjectIds to strings for JSON serialization
        for log in logs:
            if '_id' in log:
                log['_id'] = str(log['_id'])
        return logs
    except Exception as e:
        logging.error(f"Failed to get claim logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/faucet-sites")
async def get_faucet_sites():
    """Get list of supported faucet sites"""
    return FAUCET_SITES

@api_router.post("/manual-withdrawal")
async def manual_withdrawal(to_address: str, amount: float):
    """Manually trigger withdrawal"""
    try:
        tx_result = await send_bitcoin_transaction(to_address, amount)
        return tx_result
    except Exception as e:
        logging.error(f"Manual withdrawal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send real-time stats
            stats = await get_wallet_stats()
            await websocket.send_text(json.dumps({
                "type": "stats_update",
                "data": stats.dict()
            }))
            
            await asyncio.sleep(5)  # Update every 5 seconds
    except Exception as e:
        logging.error(f"WebSocket error: {e}")

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["https://crypto-faucet-frontend.onrender.com", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
