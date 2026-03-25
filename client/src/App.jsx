import { useState, useEffect } from 'react';
import './App.css';
import WorkerRecords from './components/WorkerRecords.jsx';
import AddRecord from './components/AddRecord.jsx';
import Settings from './components/Settings.jsx';

function App() {
  const [records, setRecords] = useState([]);
  const [settings, setSettings] = useState({
    hourlyRate: 200,
    breakMinutes: 60,
    vnpfEmployeeRatePercent: 6.0
  });
  const [activeTab, setActiveTab] = useState('records');

  // Load data from localStorage on mount
  useEffect(() => {
    const savedRecords = localStorage.getItem('workerRecords');
    const savedSettings = localStorage.getItem('appSettings');

    if (savedRecords) {
      setRecords(JSON.parse(savedRecords));
    }

    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  // Save records to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('workerRecords', JSON.stringify(records));
  }, [records]);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('appSettings', JSON.stringify(settings));
  }, [settings]);

  const addRecord = (record) => {
    const newRecord = {
      ...record,
      id: Date.now(),
      paid: false
    };
    setRecords([...records, newRecord]);
  };

  const deleteRecord = (id) => {
    setRecords(records.filter(record => record.id !== id));
  };

  const togglePaid = (id) => {
    setRecords(records.map(record =>
      record.id === id ? { ...record, paid: !record.paid } : record
    ));
  };

  const updateSettings = (newSettings) => {
    setSettings(newSettings);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>IHS Payslip - Worker Records</h1>
        <nav className="tabs">
          <button 
            className={activeTab === 'records' ? 'active' : ''}
            onClick={() => setActiveTab('records')}
          >
            Records
          </button>
          <button 
            className={activeTab === 'add' ? 'active' : ''}
            onClick={() => setActiveTab('add')}
          >
            Add New
          </button>
          <button 
            className={activeTab === 'settings' ? 'active' : ''}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        </nav>
      </header>

      <main className="App-main">
        {activeTab === 'records' && (
          <WorkerRecords 
            records={records} 
            settings={settings}
            onDelete={deleteRecord}
            onTogglePaid={togglePaid}
          />
        )}
        {activeTab === 'add' && (
          <AddRecord 
            onAdd={addRecord} 
            settings={settings}
          />
        )}
        {activeTab === 'settings' && (
          <Settings 
            settings={settings}
            onUpdate={updateSettings}
          />
        )}
      </main>
    </div>
  );
}

export default App;
