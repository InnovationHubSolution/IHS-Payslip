# IHS Payslip - React App Deployment Guide

## 🎉 Your React App is Ready!

A modern, responsive React application for tracking worker time and payroll with VNPF calculations.

## 📋 Features

- ✅ Track worker clock in/out times
- 💰 Automatic pay calculations with VNPF deductions
- 📊 Filter and search records
- 💾 Local storage persistence (data stays in browser)
- 📱 Responsive design for mobile and desktop
- 🎨 Modern, professional UI

## 🚀 Quick Start (Local Development)

```bash
cd client
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

## 📦 Deploy to GitHub Pages

### Option 1: Automatic Deployment (Recommended)

Your repository is already configured with GitHub Actions! Just push your code:

```bash
# From the root of your repository
git add .
git commit -m "Add React app for GitHub Pages"
git push origin main
```

**Then enable GitHub Pages:**

1. Go to your repository on GitHub: https://github.com/InnovationHubSolution/IHS-Payslip
2. Click **Settings** → **Pages** (in the sidebar)
3. Under **Source**, select **GitHub Actions**
4. Wait 2-3 minutes for the deployment to complete

Your app will be live at: **https://innovationhubsolution.github.io/IHS-Payslip/**

### Option 2: Manual Deployment

```bash
cd client
npm run build
npm install -g gh-pages  # If not already installed
npm run deploy
```

## 🔧 Configuration

The app is configured with these defaults (changeable in Settings tab):

- **Hourly Rate:** 200 VUV
- **Break Minutes:** 60 minutes
- **VNPF Rate:** 6% (employee contribution)

## 📱 How to Use

1. **Settings Tab**: Configure default hourly rate, break time, and VNPF rate
2. **Add New Tab**: Add worker records with clock in/out times
3. **Records Tab**: View all records, mark as paid, filter by name or status

## 🗂️ Project Structure

```
client/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── AddRecord.js      # Form to add new worker records
│   │   ├── WorkerRecords.js  # Display and manage records
│   │   └── Settings.js       # App configuration
│   ├── App.js                # Main app component
│   ├── App.css               # Styling
│   ├── index.js              # Entry point
│   └── index.css             # Global styles
├── package.json
└── .gitignore
```

## 💾 Data Storage

- All data is stored in browser's localStorage
- Data persists between sessions
- No backend server required
- Export/backup feature can be added in future updates

## 🔄 Future Enhancements

- Export records to CSV/PDF
- Backend API integration for multi-device sync
- Employee management system
- Payslip generation
- Report analytics and charts

## 🛠️ Technology Stack

- **React 18** - UI framework
- **Local Storage API** - Data persistence
- **GitHub Pages** - Free static hosting
- **GitHub Actions** - Automated deployments

## 📝 Notes

- This is a static React app suitable for GitHub Pages
- The Python Flask backend (`app.py`) is preserved for future API development
- To integrate with a backend later, you can deploy the Flask app to Azure/Heroku/Railway

## 🐛 Troubleshooting

**Build fails:**
- Check Node.js version (requires Node 14+)
- Delete `node_modules` and run `npm install` again

**GitHub Pages not updating:**
- Check the Actions tab for deployment status
- Ensure GitHub Pages source is set to "GitHub Actions"
- Clear browser cache

**Data not persisting:**
- Check browser settings allow localStorage
- Try a different browser

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

Made with ❤️ for Innovation Hub Solution
