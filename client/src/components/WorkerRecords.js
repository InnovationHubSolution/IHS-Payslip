import React, { useState } from 'react';

function WorkerRecords({ records, settings, onDelete, onTogglePaid }) {
    const [filterName, setFilterName] = useState('');
    const [filterPaidStatus, setFilterPaidStatus] = useState('all');

    const filteredRecords = records.filter(record => {
        const matchesName = record.workerName.toLowerCase().includes(filterName.toLowerCase());
        const matchesPaid = filterPaidStatus === 'all' ||
            (filterPaidStatus === 'paid' && record.paid) ||
            (filterPaidStatus === 'unpaid' && !record.paid);
        return matchesName && matchesPaid;
    });

    const calculateTotals = () => {
        return filteredRecords.reduce((acc, record) => {
            const hours = parseFloat(record.hoursWorked) || 0;
            const netPay = parseFloat(record.netPay) || 0;
            return {
                totalHours: acc.totalHours + hours,
                totalPay: acc.totalPay + netPay
            };
        }, { totalHours: 0, totalPay: 0 });
    };

    const totals = calculateTotals();

    return (
        <div className="card">
            <h2>Worker Records</h2>

            <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <div className="form-group" style={{ flex: '1', minWidth: '200px', marginBottom: 0 }}>
                    <label>Filter by Name</label>
                    <input
                        type="text"
                        value={filterName}
                        onChange={(e) => setFilterName(e.target.value)}
                        placeholder="Search worker name..."
                    />
                </div>

                <div className="form-group" style={{ flex: '1', minWidth: '200px', marginBottom: 0 }}>
                    <label>Filter by Status</label>
                    <select
                        value={filterPaidStatus}
                        onChange={(e) => setFilterPaidStatus(e.target.value)}
                    >
                        <option value="all">All Records</option>
                        <option value="paid">Paid Only</option>
                        <option value="unpaid">Unpaid Only</option>
                    </select>
                </div>
            </div>

            {filteredRecords.length === 0 ? (
                <p style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                    No records found. Add your first worker record!
                </p>
            ) : (
                <>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Worker Name</th>
                                    <th>In Time</th>
                                    <th>Out Time</th>
                                    <th>Hours</th>
                                    <th>Net Pay (VUV)</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredRecords.map(record => (
                                    <tr key={record.id}>
                                        <td>{record.date}</td>
                                        <td>{record.workerName}</td>
                                        <td>{record.inTime}</td>
                                        <td>{record.outTime}</td>
                                        <td>{record.hoursWorked}</td>
                                        <td>{record.netPay}</td>
                                        <td>
                                            <span className={`paid-badge ${record.paid ? 'paid' : 'unpaid'}`}>
                                                {record.paid ? 'Paid' : 'Unpaid'}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="actions">
                                                <button
                                                    onClick={() => onTogglePaid(record.id)}
                                                    className={`btn btn-small ${record.paid ? 'btn-success' : 'btn-primary'}`}
                                                >
                                                    {record.paid ? 'Mark Unpaid' : 'Mark Paid'}
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        if (window.confirm('Are you sure you want to delete this record?')) {
                                                            onDelete(record.id);
                                                        }
                                                    }}
                                                    className="btn btn-small btn-danger"
                                                >
                                                    Delete
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div style={{
                        marginTop: '1.5rem',
                        padding: '1rem',
                        background: '#f9fafb',
                        borderRadius: '8px'
                    }}>
                        <h3>Summary</h3>
                        <p><strong>Total Records:</strong> {filteredRecords.length}</p>
                        <p><strong>Total Hours:</strong> {totals.totalHours.toFixed(2)} hrs</p>
                        <p><strong>Total Net Pay:</strong> {totals.totalPay.toFixed(2)} VUV</p>
                    </div>
                </>
            )}
        </div>
    );
}

export default WorkerRecords;
