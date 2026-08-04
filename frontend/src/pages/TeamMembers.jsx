import { useState, useEffect } from 'react';
import { getTeamMembers, inviteTeamMember, updateTeamMember, removeTeamMember, resendInvite, cancelInvite } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { PermissionGuard } from '../context/PermissionContext';
import { useToast } from '../components/Toast';
import { Users, UserPlus, MagnifyingGlass, Funnel, CaretDown, CaretUp, PencilSimple, Trash, X, Prohibit, CheckCircle, EnvelopeSimple, PaperPlaneRight } from '@phosphor-icons/react';
import './TeamMembers.css';

export default function TeamMembers() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination & Filtering state
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDesc, setSortDesc] = useState(true);
  
  // Modals state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  
  // Forms state
  const [formData, setFormData] = useState({
    email: '',
    role: 'user',
    department: ''
  });
  const [editFormData, setEditFormData] = useState({});

  const fetchMembers = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        size,
        search,
        role: roleFilter,
        status: statusFilter,
        sort_by: sortBy,
        sort_desc: sortDesc
      };
      
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null) {
          delete params[key];
        }
      });
      
      const res = await getTeamMembers(params);
      setMembers(res.items);
      setTotal(res.total);
      setPages(res.pages);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch team members');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchMembers();
    }, 300);
    return () => clearTimeout(timer);
  }, [page, size, search, roleFilter, statusFilter, sortBy, sortDesc]);

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(column);
      setSortDesc(true);
    }
  };

  const handleInviteSubmit = async (e) => {
    e.preventDefault();
    try {
      await inviteTeamMember(formData);
      setShowInviteModal(false);
      setFormData({ email: '', role: 'user', department: '' });
      fetchMembers();
      showToast('Invitation sent successfully', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to invite member', 'error');
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateTeamMember(selectedMember.id, editFormData);
      setShowEditModal(false);
      fetchMembers();
      showToast('Member updated successfully', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to update member', 'error');
    }
  };

  const handleRemove = async (id) => {
    if (!window.confirm('Are you sure you want to remove this member from the workspace?')) return;
    try {
      await removeTeamMember(id);
      fetchMembers();
      showToast('Member removed from workspace', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to remove member', 'error');
    }
  };
  
  const handleToggleStatus = async (member) => {
    const newStatus = member.status === 'Active' ? 'Suspended' : 'Active';
    if (!window.confirm(`Are you sure you want to ${newStatus === 'Active' ? 'activate' : 'suspend'} this member?`)) return;
    try {
      await updateTeamMember(member.id, { status: newStatus });
      fetchMembers();
      showToast(`Member ${newStatus.toLowerCase()} successfully`, 'success');
    } catch (err) {
      showToast(err.message || `Failed to ${newStatus === 'Active' ? 'activate' : 'suspend'} member`, 'error');
    }
  };

  const handleCancelInvite = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this invitation?')) return;
    try {
      await cancelInvite(id);
      fetchMembers();
      showToast('Invitation cancelled', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to cancel invitation', 'error');
    }
  };

  const handleResendInvite = async (id) => {
    try {
      await resendInvite(id);
      showToast('Invitation resent successfully', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to resend invitation', 'error');
    }
  };

  const openEditModal = (member) => {
    setSelectedMember(member);
    setEditFormData({
      role: member.role,
      department: member.department || ''
    });
    setShowEditModal(true);
  };

  const renderSortIcon = (column) => {
    if (sortBy !== column) return null;
    return sortDesc ? <CaretDown size={14} weight="bold" /> : <CaretUp size={14} weight="bold" />;
  };

  return (
    <div className="team-members-container fade-in">
      <div className="team-header">
        <div>
          <h2><Users size={24} /> Team Members</h2>
          <p>Manage your workspace team members, roles, and pending invitations.</p>
        </div>
        <PermissionGuard permission="team.invite">
          <button className="btn-primary" onClick={() => setShowInviteModal(true)}>
            <EnvelopeSimple size={18} /> Invite Member
          </button>
        </PermissionGuard>
      </div>

      <div className="team-controls glass-card">
        <div className="search-box">
          <MagnifyingGlass size={18} />
          <input 
            type="text" 
            placeholder="Search by name or email..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="filters">
          <div className="filter-group">
            <Funnel size={18} />
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="user">User</option>
            </select>
          </div>
          <div className="filter-group">
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All Statuses</option>
              <option value="Active">Active</option>
              <option value="Suspended">Suspended</option>
              <option value="Pending">Pending Invite</option>
            </select>
          </div>
        </div>
      </div>

      <div className="table-wrapper glass-card">
        {error && <div className="error-alert">{error}</div>}
        
        <table className="team-table">
          <thead>
            <tr>
              <th>Member</th>
              <th onClick={() => handleSort('role')} className="sortable">Role {renderSortIcon('role')}</th>
              <th onClick={() => handleSort('department')} className="sortable">Department {renderSortIcon('department')}</th>
              <th onClick={() => handleSort('status')} className="sortable">Status {renderSortIcon('status')}</th>
              <th onClick={() => handleSort('last_login')} className="sortable">Last Login {renderSortIcon('last_login')}</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="text-center p-4">Loading members...</td></tr>
            ) : members.length === 0 ? (
              <tr><td colSpan="6" className="text-center p-4">No members found</td></tr>
            ) : (
              members.map(m => (
                <tr key={m.id}>
                  <td>
                    <div className="member-info">
                      <div className="avatar">
                        {m.display_name ? m.display_name.charAt(0).toUpperCase() : m.email.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="member-name">{m.display_name || (m.status === 'Pending' ? 'Invited User' : 'Unnamed User')}</div>
                        <div className="member-email">{m.email}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`role-badge ${m.role}`}>{m.role}</span>
                  </td>
                  <td>{m.department || '-'}</td>
                  <td>
                    <span className={`status-indicator ${m.status.toLowerCase()}`}>
                      {m.status}
                    </span>
                  </td>
                  <td>{m.last_login ? new Date(m.last_login).toLocaleDateString() : '-'}</td>
                  <td>
                    <div className="action-buttons">
                      {m.id !== user.id && (
                        <>
                          {m.status === 'Pending' ? (
                            <>
                              <PermissionGuard permission="team.invite">
                                <button onClick={() => handleResendInvite(m.id)} className="icon-btn" title="Resend Invite">
                                  <PaperPlaneRight size={18} />
                                </button>
                                <button onClick={() => handleCancelInvite(m.id)} className="icon-btn danger" title="Cancel Invite">
                                  <Trash size={18} />
                                </button>
                              </PermissionGuard>
                            </>
                          ) : (
                            <>
                              <PermissionGuard permission="team.change_role">
                                <button onClick={() => openEditModal(m)} className="icon-btn" title="Edit Role/Dept">
                                  <PencilSimple size={18} />
                                </button>
                              </PermissionGuard>
                              <PermissionGuard permission="team.suspend">
                                <button onClick={() => handleToggleStatus(m)} className="icon-btn" title={m.status === 'Active' ? 'Suspend' : 'Activate'}>
                                  {m.status === 'Active' ? <Prohibit size={18} color="var(--danger-color)" /> : <CheckCircle size={18} color="var(--success-color)" />}
                                </button>
                              </PermissionGuard>
                              <PermissionGuard permission="team.remove">
                                <button onClick={() => handleRemove(m.id)} className="icon-btn danger" title="Remove">
                                  <Trash size={18} />
                                </button>
                              </PermissionGuard>
                            </>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {pages > 1 && (
          <div className="pagination">
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>Prev</button>
            <span>Page {page} of {pages}</span>
            <button disabled={page === pages} onClick={() => setPage(p => p + 1)}>Next</button>
          </div>
        )}
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card slide-up">
            <div className="modal-header">
              <h3>Invite Team Member</h3>
              <button className="close-btn" onClick={() => setShowInviteModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleInviteSubmit} className="modal-form">
              <div className="form-group">
                <label>Email Address</label>
                <input required type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} placeholder="colleague@company.com" />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label>Department</label>
                <input type="text" value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} placeholder="e.g. Engineering" />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowInviteModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary"><EnvelopeSimple size={18} className="inline-block mr-1" /> Send Invitation</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedMember && (
        <div className="modal-overlay">
          <div className="modal-content glass-card slide-up">
            <div className="modal-header">
              <h3>Edit {selectedMember.display_name || selectedMember.email}</h3>
              <button className="close-btn" onClick={() => setShowEditModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleEditSubmit} className="modal-form">
              <div className="form-group">
                <label>Role</label>
                <select value={editFormData.role} onChange={e => setEditFormData({...editFormData, role: e.target.value})}>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label>Department</label>
                <input type="text" value={editFormData.department} onChange={e => setEditFormData({...editFormData, department: e.target.value})} />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowEditModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
