// src/components/StaffDashboard/DetailsView.jsx

function DetailsView({ show, onClose, swapRequests, onActionClick }) {
  if (!show) return null;

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED': return <span className="badge bg-success">אושר</span>;
      case 'REJECTED': return <span className="badge bg-danger">נדחה</span>;
      default: return <span className="badge bg-warning text-dark">ממתין לאישור</span>;
    }
  };

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-dialog-centered modal-lg" dir="rtl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title fw-bold">🔄 ניהול בקשות החלפה ({Array.isArray(swapRequests) ? swapRequests.length : 0})</h5>
            <button type="button" className="btn-close m-0" onClick={onClose}></button>
          </div>
          <div className="modal-body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
            {!Array.isArray(swapRequests) || swapRequests.length === 0 ? (
              <p className="text-muted text-center py-4">אין בקשות החלפה ממתינות</p>
            ) : (
              <div className="d-flex flex-column gap-3">
                {swapRequests.map((req) => {
                  const reqId = req.request_id || req.id;
                  return (
                    <div key={reqId} className="p-3 bg-light rounded border small">
                      <div className="d-flex justify-content-between align-items-center mb-1">
                        <span className="fw-bold text-dark">{req.student_name || 'סטודנט'}</span>
                        {renderStatusBadge(req.status)}
                      </div>
                      <div className="text-secondary mb-2">
                        <div><strong>נוכחית:</strong> {req.current_topic_name || req.current_schedule_id}</div>
                        <div><strong>מבוקשת:</strong> {req.target_topic_name || req.target_schedule_id}</div>
                        <div className="text-muted mt-1"><strong>סיבה:</strong> {req.reason}</div>
                      </div>

                      {req.status === 'PENDING' && (
                        <div className="d-flex gap-2 pt-2 border-top">
                          <button 
                            type="button"
                            className="btn btn-success btn-sm py-1 px-3"
                            onClick={() => onActionClick(reqId, 'APPROVED')}
                          >
                            אשר ✓
                          </button>
                          <button 
                            type="button"
                            className="btn btn-danger btn-sm py-1 px-3"
                            onClick={() => onActionClick(reqId, 'REJECTED')}
                          >
                            דחה ✕
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>סגור</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DetailsView;