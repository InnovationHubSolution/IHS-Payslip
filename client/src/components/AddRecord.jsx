import React, { useState } from 'react';

function AddRecord({ onAdd, settings }) {
    const [formData, setFormData] = useState({
        date: new Date().toISOString().split('T')[0],
        workerName: '',
        inTime: '',
        outTime: ''
    });

    const calculatePay = () => {
        if (!formData.inTime || !formData.outTime) return null;

        const inMinutes = timeToMinutes(formData.inTime);
        const outMinutes = timeToMinutes(formData.outTime);

        let workedMinutes = outMinutes - inMinutes;
        if (workedMinutes < 0) workedMinutes += 24 * 60; // Handle overnight shifts

        const breakMinutes = settings.breakMinutes || 0;
        const netMinutes = workedMinutes - breakMinutes;
        const hoursWorked = netMinutes / 60;

        const grossPay = hoursWorked * (settings.hourlyRate || 0);
        const vnpfDeduction = (grossPay * (settings.vnpfEmployeeRatePercent || 0)) / 100;
        const netPay = grossPay - vnpfDeduction;

        return {
            hoursWorked: hoursWorked.toFixed(2),
            grossPay: grossPay.toFixed(2),
            vnpfDeduction: vnpfDeduction.toFixed(2),
            netPay: netPay.toFixed(2)
        };
    };

    const timeToMinutes = (timeStr) => {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + minutes;
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        const pay = calculatePay();
        if (!pay) {
            alert('Please fill in all fields');
            return;
        }

        const record = {
            ...formData,
            ...pay,
            breakMinutes: settings.breakMinutes || 0,
            hourlyRate: settings.hourlyRate || 0,
            timestamp: new Date().toISOString()
        };

        onAdd(record);

        // Reset form
        setFormData({
            date: new Date().toISOString().split('T')[0],
            workerName: '',
            inTime: '',
            outTime: ''
        });

        alert('Record added successfully!');
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const preview = calculatePay();

    return (
        <div className="card">
            <h2>Add New Worker Record</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Date</label>
                    <input
                        type="date"
                        name="date"
                        value={formData.date}
                        onChange={handleChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Worker Name</label>
                    <input
                        type="text"
                        name="workerName"
                        value={formData.workerName}
                        onChange={handleChange}
                        placeholder="Enter worker name"
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Clock In Time</label>
                    <input
                        type="time"
                        name="inTime"
                        value={formData.inTime}
                        onChange={handleChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Clock Out Time</label>
                    <input
                        type="time"
                        name="outTime"
                        value={formData.outTime}
                        onChange={handleChange}
                        required
                    />
                </div>

                {preview && (
                    <div style={{
                        background: '#f0f9ff',
                        padding: '1rem',
                        borderRadius: '8px',
                        marginBottom: '1rem'
                    }}>
                        <h3>Pay Calculation Preview</h3>
                        <p><strong>Hours Worked:</strong> {preview.hoursWorked} hrs</p>
                        <p><strong>Hourly Rate:</strong> {settings.hourlyRate} VUV</p>
                        <p><strong>Break Minutes:</strong> {settings.breakMinutes} min</p>
                        <p><strong>Gross Pay:</strong> {preview.grossPay} VUV</p>
                        <p><strong>VNPF Deduction ({settings.vnpfEmployeeRatePercent}%):</strong> {preview.vnpfDeduction} VUV</p>
                        <p><strong>Net Pay:</strong> {preview.netPay} VUV</p>
                    </div>
                )}

                <button type="submit" className="btn btn-primary">
                    Add Record
                </button>
            </form>
        </div>
    );
}

export default AddRecord;
