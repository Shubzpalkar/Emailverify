import { useState, useEffect } from 'react';
import { getWorkspaceSettings, updateWorkspaceSettings } from '../api/client';
import { useToast } from '../components/Toast';
import { PermissionGuard } from '../context/PermissionContext';

export default function WorkspaceSettings() {
  const [formData, setFormData] = useState({
    company_name: '',
    industry: '',
    company_size: '',
    website: '',
    country: '',
    timezone: '',
    language: 'en'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    async function fetchSettings() {
      try {
        const data = await getWorkspaceSettings();
        setFormData({
          company_name: data.company_name || '',
          industry: data.industry || '',
          company_size: data.company_size || '',
          website: data.website || '',
          country: data.country || '',
          timezone: data.timezone || '',
          language: data.language || 'en'
        });
      } catch (error) {
        showToast('Failed to load workspace settings', 'error');
      } finally {
        setLoading(false);
      }
    }
    fetchSettings();
  }, [showToast]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateWorkspaceSettings(formData);
      showToast('Workspace settings updated successfully', 'success');
    } catch (error) {
      showToast('Failed to update workspace settings: ' + error.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading settings...</div>;

  return (
    <div className="max-w-4xl">
      <h2 className="text-2xl font-bold mb-6">Workspace Settings</h2>
      
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* General Information Card */}
        <div className="glass-card p-6">
          <h3 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">General Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="form-group">
              <label className="block text-sm font-medium text-gray-300 mb-1">Company Name</label>
              <input type="text" name="company_name" value={formData.company_name} onChange={handleChange} className="form-control w-full bg-gray-800 border-gray-700 rounded p-2" required />
            </div>
            <div className="form-group">
              <label className="block text-sm font-medium text-gray-300 mb-1">Website</label>
              <input type="url" name="website" value={formData.website} onChange={handleChange} className="form-control w-full bg-gray-800 border-gray-700 rounded p-2" />
            </div>
            <div className="form-group">
              <label className="block text-sm font-medium text-gray-300 mb-1">Industry</label>
              <input type="text" name="industry" value={formData.industry} onChange={handleChange} className="form-control w-full bg-gray-800 border-gray-700 rounded p-2" />
            </div>
            <div className="form-group">
              <label className="block text-sm font-medium text-gray-300 mb-1">Company Size</label>
              <select name="company_size" value={formData.company_size} onChange={handleChange} className="form-control w-full bg-gray-800 border-gray-700 rounded p-2">
                <option value="">Select size</option>
                <option value="1-10">1-10 employees</option>
                <option value="11-50">11-50 employees</option>
                <option value="51-200">51-200 employees</option>
                <option value="201-500">201-500 employees</option>
                <option value="500+">500+ employees</option>
              </select>
            </div>
          </div>
        </div>

        {/* Branding Card */}
        <div className="glass-card p-6">
          <h3 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Branding</h3>
          <p className="text-gray-400 mb-4">Company logo and colors will appear on shared reports and invoices.</p>
          <div className="flex items-center space-x-4">
             <div className="w-16 h-16 bg-gray-800 rounded flex items-center justify-center border border-gray-700 text-gray-500">
               Logo
             </div>
             <button type="button" className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded border border-gray-700 transition">Upload New Logo</button>
          </div>
        </div>

        {/* Localization & Region */}
        <div className="glass-card p-6">
          <h3 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Localization</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="form-group">
              <label className="block text-sm font-medium text-gray-300 mb-1">Country</label>
              <input type="text" name="country" value={formData.country} onChange={handleChange} className="form-control w-full bg-gray-800 border-gray-700 rounded p-2" />
            </div>
            <div className="form-group">
              <label className="block text-sm font-medium text-gray-300 mb-1">Timezone</label>
              <input type="text" name="timezone" value={formData.timezone} onChange={handleChange} className="form-control w-full bg-gray-800 border-gray-700 rounded p-2" />
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <PermissionGuard permission="workspace.update">
            <button type="submit" disabled={saving} className="btn-primary px-6 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium transition">
              {saving ? 'Saving...' : 'Save Workspace Settings'}
            </button>
          </PermissionGuard>
        </div>
      </form>
    </div>
  );
}
