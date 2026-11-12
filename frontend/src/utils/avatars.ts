// Curated high-resolution professional enterprise avatars (Unsplash)
export const PERSONA_AVATARS: Record<string, string> = {
  // Key Demo Personas
  'employee@leaveflow.internal': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=256&h=256&q=80', // Sarah Connor
  'manager@leaveflow.internal': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=256&h=256&q=80', // David Kim
  'finance@leaveflow.internal': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=256&h=256&q=80', // Claire Redfield
  'process.owner@leaveflow.internal': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=256&h=256&q=80', // Marcus Sterling
  'admin@leaveflow.internal': 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=256&h=256&q=80', // Eleanor Vance

  // Role fallbacks
  EMPLOYEE: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=256&h=256&q=80',
  MANAGER: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=256&h=256&q=80',
  FINANCE: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=256&h=256&q=80',
  PROCESS_OWNER: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=256&h=256&q=80',
  ADMIN: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=256&h=256&q=80',
};

// Array of diverse professional portraits for employee lists and testimonials
export const TEAM_PORTRAITS = [
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=256&h=256&q=80',
  'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=256&h=256&q=80',
];

export const TESTIMONIALS = [
  {
    name: 'Priya Sharma',
    role: 'VP of People Operations',
    company: 'FinTech Nexus Inc.',
    image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=256&h=256&q=80',
    quote: 'LeaveFlow replaced our fragile multi-tool leave nightmare with an explainable, deterministic graph. Employee disputes dropped to zero because every calculation provides mathematical evidence.',
    stats: '85% faster approvals',
    rating: 5,
  },
  {
    name: 'Michael Chen',
    role: 'Chief Financial Officer',
    company: 'CloudScale Global',
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=256&h=256&q=80',
    quote: 'The dual-ledger atomic reservations and split-claim heuristics saved us over $140,000 in unbudgeted expense leakage in the first quarter alone. The SHA-256 audit chain satisfied our Big 4 auditors on day one.',
    stats: '$140k saved in Q1',
    rating: 5,
  },
  {
    name: 'Elena Rostova',
    role: 'Director of Compliance & Internal Audit',
    company: 'Apex Health Systems',
    image: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=256&h=256&q=80',
    quote: 'Zero self-approval enforcement and tamper-evident cryptographic block hashes give us complete peace of mind. We can verify 10,000 historic transactions in seconds without manual spreadsheets.',
    stats: '100% audit compliance',
    rating: 5,
  },
];

export function getAvatarUrl(identifier?: string, role?: string): string {
  if (identifier && PERSONA_AVATARS[identifier]) {
    return PERSONA_AVATARS[identifier];
  }
  if (role && PERSONA_AVATARS[role]) {
    return PERSONA_AVATARS[role];
  }
  if (!identifier) {
    return TEAM_PORTRAITS[0];
  }
  // Deterministic index from string identifier
  let hash = 0;
  for (let i = 0; i < identifier.length; i++) {
    hash = identifier.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % TEAM_PORTRAITS.length;
  return TEAM_PORTRAITS[index];
}
