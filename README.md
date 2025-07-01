# 🚀 Crypto Faucet Auto-Claimer

A fully automated crypto faucet claiming system with real Bitcoin withdrawals, supporting 100+ faucet websites with proxy rotation and CAPTCHA solving.

## ✨ Features

- 🎯 **116+ Faucet Sites** - Automated claiming from major faucets
- 🔄 **Multi-Session Support** - Run 1-10,000 concurrent sessions
- ₿ **Real BTC Withdrawals** - Auto-withdrawal at 0.0000093 BTC threshold
- 🌐 **Free Proxy Rotation** - Built-in proxy rotation system
- 🧠 **CAPTCHA Solving** - OpenCV + Tesseract integration
- 📊 **Real-time Dashboard** - Live stats updating every 5 seconds
- 🔗 **Blockchain Integration** - Direct Bitcoin transactions via Blockstream API
- 🤖 **24/7 Automation** - Background claiming with session management

## 🏗️ Tech Stack

- **Frontend**: React + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: MongoDB
- **Browser Automation**: Playwright
- **CAPTCHA Solving**: OpenCV + Tesseract
- **Blockchain**: Blockstream API (no API keys needed)

## 📁 Project Structure

```
/app/
├── backend/
│   ├── server.py          # Main FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment variables
├── frontend/
│   ├── src/
│   │   ├── App.js        # Main React component
│   │   └── App.css       # Styling
│   ├── package.json      # Node.js dependencies
│   └── .env             # Frontend environment
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB
- Tesseract OCR

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

### Frontend Setup

```bash
cd frontend
yarn install
```

### Environment Variables

**Backend (.env)**:
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="crypto_faucet"
```

**Frontend (.env)**:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🎯 Supported Faucet Sites (116+)

Major supported faucets include:
- Cointiply, FireFaucet, FaucetCrypto
- Freebitco.in, BonusBitcoin, Bitcoinker
- MoonBitcoin, FreeLitecoin, FreeEthereum
- Pipeflare, TrustDice, ExpressCrypto
- And 100+ more popular faucet sites!

## 🔧 API Endpoints

### Core Endpoints
- `GET /api/` - Health check
- `GET /api/wallet-stats` - Wallet statistics
- `GET /api/faucet-sites` - List of supported faucets
- `GET /api/claim-logs` - Recent claim logs

### Session Management
- `POST /api/start-session` - Start claiming sessions
- `GET /api/session-status/{session_id}` - Get session status
- `DELETE /api/stop-session/{session_id}` - Stop session

### Withdrawals
- `POST /api/manual-withdrawal` - Manual BTC withdrawal
- Auto-withdrawal at 0.0000093 BTC threshold

## 📊 Dashboard Features

- **Live Balance Tracking** - Real-time BTC balance
- **Session Control** - Start/stop with custom session count
- **Claims Monitoring** - Live claim logs and statistics
- **Faucet Status** - Monitor all supported faucets
- **Auto-withdrawal Display** - Current threshold and wallet info

## ⚙️ Configuration

### Session Configuration
```json
{
  "session_count": 100,
  "auto_withdrawal": true,
  "withdrawal_threshold": 0.0000093,
  "withdrawal_address": "bc1qzh55yrw9z4ve9zxy04xuw9mq838g5c06tqvrxk",
  "proxy_enabled": true,
  "captcha_solving": true
}
```

### Proxy Rotation
Built-in free proxy rotation with automatic failover:
- 8+ free proxy servers included
- Automatic proxy rotation per session
- Fallback to direct connection if proxies fail

### CAPTCHA Solving
OpenCV + Tesseract integration:
- Automatic image preprocessing
- OCR text extraction
- 60-80% success rate on simple CAPTCHAs

## 🔒 Security Features

- Environment variable protection
- MongoDB document sanitization
- Secure transaction handling
- Error logging and monitoring

## 📈 Performance

- **Concurrent Sessions**: Up to 10,000 simultaneous sessions
- **Real-time Updates**: Dashboard updates every 5 seconds
- **Background Processing**: Non-blocking session management
- **Auto-scaling**: Dynamic session allocation

## 🌐 Deployment

### Local Development
```bash
# Backend
cd backend && python server.py

# Frontend  
cd frontend && yarn start
```

### Production Deployment
- Deploy backend to any Python hosting service
- Deploy frontend to static hosting (Netlify, Vercel)
- Configure MongoDB connection
- Set up environment variables

## 🔧 Dependencies

### Backend Requirements
- fastapi==0.110.1
- playwright>=1.40.0
- opencv-python>=4.8.0
- pytesseract>=0.3.10
- bitcoinlib>=0.7.4
- motor==3.3.1

### Frontend Dependencies
- React 18
- Axios for API calls
- Tailwind CSS for styling
- Real-time WebSocket updates

## ⚠️ Legal Notice

This software is for educational purposes. Users are responsible for:
- Compliance with faucet Terms of Service
- Legal requirements in their jurisdiction
- Responsible usage of automation tools

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🚀 Getting Started

1. **Clone the repository**
2. **Install dependencies** (backend + frontend)
3. **Configure environment variables**
4. **Start the application**
5. **Access dashboard** and start claiming!

## 💡 Features in Detail

### Multi-Session Management
- Start up to 10,000 concurrent claiming sessions
- Each session runs independently with its own browser instance
- Real-time monitoring of all active sessions

### Intelligent Claiming
- Automatic cooldown tracking per faucet
- Smart retry logic for failed claims
- CAPTCHA detection and solving attempts

### Blockchain Integration
- Direct Bitcoin transactions using Blockstream API
- No third-party wallet services required
- Real-time balance tracking and auto-withdrawals

### Monitoring & Analytics
- Comprehensive logging of all claiming attempts
- Success/failure rate tracking
- Earnings analytics and projections

---

**Ready to start earning crypto automatically? Deploy and start claiming from 116+ faucets today!** 🚀₿