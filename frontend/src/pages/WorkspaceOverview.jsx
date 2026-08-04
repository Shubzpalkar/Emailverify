import { useState, useEffect } from 'react';
import { getWorkspace } from '../api/client';
import { useToast } from '../components/Toast';

export default function WorkspaceOverview() {
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    async function fetchWorkspace() {
      try {
        const data = await getWorkspace();
        setWorkspace(data);
      } catch (error) {
        showToast('Failed to load workspace data: ' + error.message, 'error');
      } finally {
        setLoading(false);
      }
    }
    fetchWorkspace();
  }, [showToast]);

  if (loading) return <div>Loading workspace...</div>;
  if (!workspace) return <div>No workspace found.</div>;

  return (
    <div className="glass-card p-8">
      <h2 className="text-2xl font-bold mb-4">Workspace Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">Company Name</h3>
          <p className="text-xl font-semibold">{workspace.company_name}</p>
        </div>
        
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">Status</h3>
          <p className="text-xl font-semibold text-green-400">{workspace.workspace_status}</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">Current Plan</h3>
          <p className="text-xl font-semibold">{workspace.plan}</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">Credits Remaining</h3>
          <p className="text-xl font-semibold text-blue-400">{workspace.credits_remaining.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
