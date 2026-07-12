import { useState, useEffect } from 'react';
import { getAPIKeys, createAPIKey, revokeAPIKey } from '../api/client';
import { useToast } from '../components/Toast';
import { Key, Plus, Trash, Copy, Check, Warning } from '@phosphor-icons/react';
import './APIKeys.css';

export default function APIKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [generatedKey, setGeneratedKey] = useState(null);
  const [copied, setCopied] = useState(false);
  const { showToast } = useToast();

  const fetchKeys = async () => {
    try {
      const data = await getAPIKeys();
      setKeys(data);
    } catch {
      showToast('Failed to fetch API keys', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreateKey = async (e) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;

    try {
      const data = await createAPIKey(newKeyName);
      setGeneratedKey(data);
      setNewKeyName('');
      fetchKeys();
    } catch (err) {
      showToast(err.message || 'Failed to create key', 'error');
    }
  };

  const handleRevokeKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to revoke this API key? Programmatic access using this key will stop immediately.')) return;

    try {
      await revokeAPIKey(keyId);
      showToast('Key revoked successfully');
      fetchKeys();
    } catch {
      showToast('Failed to revoke key', 'error');
    }
  };

  const copyToClipboard = () => {
    if (!generatedKey?.key) return;
    navigator.clipboard.writeText(generatedKey.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    showToast('Key copied to clipboard');
  };

  return (
    <div className="container page-enter api-keys-page">
      <div className="dashboard-header">
        <div>
          <h2>API Keys</h2>
          <p>Manage your keys for programmatic access to the verification engine.</p>
        </div>
        <button className="btn-primary btn-small" onClick={() => setShowModal(true)}>
          <Plus size={18} weight="bold" />
          Create New Key
        </button>
      </div>

      <div className="glass-card keys-list">
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Prefix</th>
                <th>Created</th>
                <th>Last Used</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="5" style={{ textAlign: 'center' }}>Loading keys...</td></tr>
              ) : keys.length === 0 ? (
                <tr><td colSpan="5" style={{ textAlign: 'center' }}>No API keys found. Create one to get started.</td></tr>
              ) : (
                keys.map(k => (
                  <tr key={k.id}>
                    <td><strong>{k.name}</strong></td>
                    <td><code className="key-code">{k.prefix}</code></td>
                    <td>{new Date(k.created_at).toLocaleDateString()}</td>
                    <td>{k.last_used ? new Date(k.last_used).toLocaleString() : 'Never'}</td>
                    <td>
                      <button className="btn-icon btn-danger" onClick={() => handleRevokeKey(k.id)} title="Revoke Key">
                        <Trash size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="glass-card modal-content auth-card">
            {generatedKey ? (
              <div className="key-success">
                <h3>Key Created Successfully!</h3>
                <div className="warning-banner">
                  <Warning size={24} weight="fill" />
                  <p>Save this key now. For security reasons, <strong>it will not be shown again.</strong></p>
                </div>
                <div className="key-display-box">
                  <pre>{generatedKey.key}</pre>
                  <button className="btn-icon" onClick={copyToClipboard}>
                    {copied ? <Check size={20} color="var(--success)" /> : <Copy size={20} />}
                  </button>
                </div>
                <button className="btn-primary btn-full" onClick={() => { setShowModal(false); setGeneratedKey(null); }}>
                  I've saved it
                </button>
              </div>
            ) : (
              <div className="key-setup">
                <h3>Create New API Key</h3>
                <p>Give your key a descriptive name to help you identify it later.</p>
                <form onSubmit={handleCreateKey}>
                  <div className="input-group" style={{ marginTop: '1.5rem' }}>
                    <label>Key Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Production Backend"
                      value={newKeyName}
                      onChange={e => setNewKeyName(e.target.value)}
                      autoFocus
                      required
                    />
                  </div>
                  <div className="modal-actions" style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                    <button type="button" className="btn-secondary btn-full" onClick={() => setShowModal(false)}>Cancel</button>
                    <button type="submit" className="btn-primary btn-full">Generate Key</button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
