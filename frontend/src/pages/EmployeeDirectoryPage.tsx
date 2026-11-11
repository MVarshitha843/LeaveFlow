import React, { useState, useEffect } from 'react';
import { employeeApi } from '../services/api';
import { User, Department } from '../types';
import { Users, Search, Building, Mail, Shield, UserCheck } from 'lucide-react';

export const EmployeeDirectoryPage: React.FC = () => {
  const [employees, setEmployees] = useState<any[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [search, deptFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [empRes, deptRes] = await Promise.all([
        employeeApi.list({ search: search || undefined, department_id: deptFilter || undefined }),
        employeeApi.departments(),
      ]);
      setEmployees(empRes.data);
      setDepartments(deptRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" />
            <span>Personnel & Organizational Directory</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Active corporate employees, reporting hierarchies, and authority structures.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, ID or email..."
              className="pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 w-56 text-slate-800"
            />
          </div>

          <select
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-300 bg-white text-slate-700"
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
              <th className="py-3 px-4">Employee ID</th>
              <th className="py-3 px-4">Name</th>
              <th className="py-3 px-4">Role</th>
              <th className="py-3 px-4">Department</th>
              <th className="py-3 px-4">Reports To (Manager)</th>
              <th className="py-3 px-4">Grade</th>
              <th className="py-3 px-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {loading ? (
              <tr><td colSpan={7} className="py-12 text-center text-slate-400">Loading directory...</td></tr>
            ) : employees.map((emp) => (
              <tr key={emp.id} className="hover:bg-slate-50 transition">
                <td className="py-3 px-4 font-mono font-bold text-blue-600">{emp.id}</td>
                <td className="py-3 px-4 font-semibold text-slate-900">
                  {emp.first_name} {emp.last_name}
                  <span className="block text-[11px] font-normal text-slate-400">{emp.email}</span>
                </td>
                <td className="py-3 px-4">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    {emp.role.replace('_', ' ')}
                  </span>
                </td>
                <td className="py-3 px-4">{emp.department_name || emp.department_id || '—'}</td>
                <td className="py-3 px-4 text-slate-600">{emp.manager_name || 'Executive Officer'}</td>
                <td className="py-3 px-4 font-mono font-semibold">{emp.grade}</td>
                <td className="py-3 px-4">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {emp.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
