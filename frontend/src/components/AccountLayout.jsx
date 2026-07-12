import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserCircle, Gear, ShieldCheck, CreditCard, Key, ChartLineUp, Trash } from '@phosphor-icons/react';
import './AccountLayout.css';

export default function AccountLayout() {
  const { user } = useAuth();
  
  if (!user) return null;

  return (
    <div className="container page-enter account-layout-wrapper">
      <div className="account-sidebar glass-card">
        <h3>Account Center</h3>
        <nav className="account-nav">
          <NavLink to="/account/profile" className={({isActive}) => isActive ? "account-nav-link active" : "account-nav-link"}>
            <UserCircle size={20} /> Profile
          </NavLink>
          <NavLink to="/account/settings" className={({isActive}) => isActive ? "account-nav-link active" : "account-nav-link"}>
            <Gear size={20} /> Settings
          </NavLink>
          <NavLink to="/account/security" className={({isActive}) => isActive ? "account-nav-link active" : "account-nav-link"}>
            <ShieldCheck size={20} /> Security
          </NavLink>
          <NavLink to="/account/billing" className={({isActive}) => isActive ? "account-nav-link active" : "account-nav-link"}>
            <CreditCard size={20} /> Billing
          </NavLink>
          <NavLink to="/account/api" className={({isActive}) => isActive ? "account-nav-link active" : "account-nav-link"}>
            <Key size={20} /> API
          </NavLink>
          <NavLink to="/account/usage" className={({isActive}) => isActive ? "account-nav-link active" : "account-nav-link"}>
            <ChartLineUp size={20} /> Usage
          </NavLink>
          <div className="account-nav-divider"></div>
          <NavLink to="/account/delete" className={({isActive}) => isActive ? "account-nav-link danger-link active" : "account-nav-link danger-link"}>
            <Trash size={20} /> Delete Account
          </NavLink>
        </nav>
      </div>
      
      <div className="account-content">
        <Outlet />
      </div>
    </div>
  );
}
