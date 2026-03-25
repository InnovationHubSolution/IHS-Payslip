import React, { useState } from 'react';

function Settings({ settings, onUpdate }) {
    const [formData, setFormData] = useState(settings);

    const handleSubmit = (e) => {
        e.preventDefault();
        onUpdate(formData);
        alert('Settings saved successfully!');
    };

    const handleChange = (e) => {
        const value = parseFloat(e.target.value) || 0;
        setFormData({
            ...formData,
            [e.target.name]: value
        });
    };

    return (
        <div className="card">
            <h2>Settings</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Hourly Rate (VUV)</label>
                    <input
                        type="number"
                        name="hourlyRate"
                        value={formData.hourlyRate}
                        onChange={handleChange}
                        step="0.01"
                        min="0"
                        required
                    />
                    <small style={{ color: '#666' }}>Default hourly rate for all workers</small>
                </div>

                <div className="form-group">
                    <label>Break Minutes</label>
                    <input
                        type="number"
                        name="breakMinutes"
                        value={formData.breakMinutes}
                        onChange={handleChange}
                        min="0"
                        required
                    />
                    <small style={{ color: '#666' }}>Default break time deducted from total hours</small>
                </div>

                <div className="form-group">
                    <label>VNPF Employee Rate (%)</label>
                    <input
                        type="number"
                        name="vnpfEmployeeRatePercent"
                        value={formData.vnpfEmployeeRatePercent}
                        onChange={handleChange}
                        step="0.1"
                        min="0"
                        max="100"
                        required
                    />
                    <small style={{ color: '#666' }}>
                        Vanuatu National Provident Fund employee contribution rate (typically 6%)
                    </small>
                </div>

                <button type="submit" className="btn btn-primary">
                    Save Settings
                </button>
            </form>

            <div style={{
                marginTop: '2rem',
                padding: '1rem',
                background: '#fffbeb',
                borderRadius: '8px',
                border: '1px solid #fbbf24'
            }}>
                <h3>ℹ️ About These Settings</h3>
                <p><strong>Hourly Rate:</strong> The base pay rate per hour in Vanuatu Vatu (VUV)</p>
                <p><strong>Break Minutes:</strong> Unpaid break time automatically deducted from work hours</p>
                <p><strong>VNPF Rate:</strong> Employee contribution to Vanuatu National Provident Fund, deducted from gross pay</p>
                <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#92400e' }}>
                    💡 All records use these default settings at the time they are created.
                </p>
            </div>
        </div>
    );
}

export default Settings;
