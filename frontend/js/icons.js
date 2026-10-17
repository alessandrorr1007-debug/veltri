/**
 * Set de íconos vectoriales locales (estilo Lucide).
 * Sin emojis y sin dependencias CDN externas.
 */

const Icons = {
  svg(pathContent, size = 16, className = '') {
    return `<svg class="icon ${className}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${pathContent}</svg>`;
  },

  cpu(size = 16, cls = '') {
    return this.svg(
      '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
      size, cls
    );
  },

  shieldCheck(size = 16, cls = '') {
    return this.svg(
      '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
      size, cls
    );
  },

  terminal(size = 16, cls = '') {
    return this.svg(
      '<polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>',
      size, cls
    );
  },

  users(size = 16, cls = '') {
    return this.svg(
      '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
      size, cls
    );
  },

  activity(size = 16, cls = '') {
    return this.svg(
      '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2"/>',
      size, cls
    );
  },

  sun(size = 16, cls = '') {
    return this.svg(
      '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
      size, cls
    );
  },

  moon(size = 16, cls = '') {
    return this.svg(
      '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
      size, cls
    );
  },

  checkCircle(size = 16, cls = '') {
    return this.svg(
      '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
      size, cls
    );
  },

  alertTriangle(size = 16, cls = '') {
    return this.svg(
      '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/>',
      size, cls
    );
  },

  xCircle(size = 16, cls = '') {
    return this.svg(
      '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
      size, cls
    );
  },

  code(size = 16, cls = '') {
    return this.svg(
      '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
      size, cls
    );
  },

  copy(size = 16, cls = '') {
    return this.svg(
      '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
      size, cls
    );
  },

  x(size = 16, cls = '') {
    return this.svg(
      '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
      size, cls
    );
  },

  check(size = 16, cls = '') {
    return this.svg(
      '<polyline points="20 6 9 17 4 12"/>',
      size, cls
    );
  },

  send(size = 16, cls = '') {
    return this.svg(
      '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
      size, cls
    );
  },

  info(size = 16, cls = '') {
    return this.svg(
      '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
      size, cls
    );
  },

  message(size = 16, cls = '') {
    return this.svg(
      '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
      size, cls
    );
  },
};
