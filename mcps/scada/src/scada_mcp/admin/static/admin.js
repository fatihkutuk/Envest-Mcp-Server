/* ========================================
   Envest MCP Admin Panel - Enhanced JS
   Modern interactions & animations
   ======================================== */

/* --- Sidebar Toggle (Mobile) --- */
function toggleSidebar() {
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  if (!sidebar) return;

  var isOpen = sidebar.classList.contains('open');
  if (isOpen) {
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = '';
  } else {
    sidebar.classList.add('open');
    if (overlay) overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

/* --- Toast Notification System --- */
var toastContainer = null;

function ensureToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }
  return toastContainer;
}

function showToast(message, type) {
  type = type || 'success';
  var container = ensureToastContainer();
  var toast = document.createElement('div');
  toast.className = 'toast toast-' + type;

  var icons = {
    success: '<svg class="w-5 h-5 text-emerald-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
    error: '<svg class="w-5 h-5 text-rose-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
    info: '<svg class="w-5 h-5 text-blue-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
  };

  toast.innerHTML = (icons[type] || icons.info) + '<span>' + message + '</span>';
  container.appendChild(toast);

  setTimeout(function() {
    toast.classList.add('removing');
    setTimeout(function() {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }, 3000);
}

/* --- Copy to Clipboard with Toast --- */
function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function() {
      showToast('Panoya kopyalandi!', 'success');
    });
  } else {
    var ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('Panoya kopyalandi!', 'success');
  }
}

function copyToClipboard(elementId) {
  var el = document.getElementById(elementId);
  if (!el) return;

  var text = el.value || el.textContent;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function() {
      showToast('Panoya kopyalandi!', 'success');
      showCopyFeedback();
    }).catch(function() {
      fallbackCopy(el);
    });
  } else {
    fallbackCopy(el);
  }
}

function fallbackCopy(el) {
  el.select();
  document.execCommand('copy');
  showToast('Panoya kopyalandi!', 'success');
  showCopyFeedback();
}

function showCopyFeedback() {
  var btn = document.getElementById('copy-btn');
  if (!btn) return;
  var original = btn.innerHTML;
  btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Kopyalandi!';
  btn.disabled = true;
  setTimeout(function() {
    btn.innerHTML = original;
    btn.disabled = false;
  }, 2000);
}

/* --- Modal with Fade-in/Scale Animation --- */
function openModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

/* --- Custom Confirmation Dialog --- */
function showConfirm(title, message, onConfirm, confirmText, confirmClass) {
  confirmText = confirmText || 'Onayla';
  confirmClass = confirmClass || 'bg-rose-500 hover:bg-rose-600';

  var overlay = document.createElement('div');
  overlay.className = 'confirm-dialog-overlay';
  overlay.innerHTML =
    '<div class="confirm-dialog">' +
    '  <div class="flex items-center gap-3 mb-4">' +
    '    <div class="w-10 h-10 rounded-full bg-rose-500/10 flex items-center justify-center shrink-0">' +
    '      <svg class="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>' +
    '    </div>' +
    '    <div>' +
    '      <h3 class="text-slate-100 font-semibold text-base">' + title + '</h3>' +
    '      <p class="text-slate-400 text-sm mt-1">' + message + '</p>' +
    '    </div>' +
    '  </div>' +
    '  <div class="flex justify-end gap-3 mt-6">' +
    '    <button class="cancel-btn px-4 py-2 rounded-lg text-sm font-medium text-slate-300 bg-white/5 border border-white/10 hover:bg-white/10 transition-all">Iptal</button>' +
    '    <button class="confirm-btn px-4 py-2 rounded-lg text-sm font-medium text-white ' + confirmClass + ' transition-all">' + confirmText + '</button>' +
    '  </div>' +
    '</div>';

  document.body.appendChild(overlay);

  // Trigger animation
  requestAnimationFrame(function() {
    overlay.classList.add('active');
  });

  var closeOverlay = function() {
    overlay.classList.remove('active');
    setTimeout(function() {
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
    }, 250);
  };

  overlay.querySelector('.cancel-btn').addEventListener('click', closeOverlay);
  overlay.querySelector('.confirm-btn').addEventListener('click', function() {
    closeOverlay();
    if (onConfirm) onConfirm();
  });

  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) closeOverlay();
  });
}

/* --- Confirmation Dialogs --- */
function confirmDelete(name) {
  var form = event.target.closest('form');
  event.preventDefault();
  showConfirm(
    'Silmeyi Onayla',
    '"' + name + '" kalici olarak silinecek. Bu islem geri alinamaz.',
    function() { form.submit(); },
    'Sil',
    'bg-rose-500 hover:bg-rose-600'
  );
  return false;
}

function confirmRevoke(name) {
  var form = event.target.closest('form');
  event.preventDefault();
  showConfirm(
    'Token Iptal',
    '"' + name + '" tokeni iptal edilecek. Bu islem geri alinamaz.',
    function() { form.submit(); },
    'Iptal Et',
    'bg-rose-500 hover:bg-rose-600'
  );
  return false;
}

/* --- Auto-hide Flash Messages --- */
document.addEventListener('DOMContentLoaded', function() {
  var flash = document.getElementById('flash-msg');
  if (flash) {
    flash.classList.add('flash-animate-in');
    setTimeout(function() {
      flash.classList.remove('flash-animate-in');
      flash.classList.add('flash-animate-out');
      setTimeout(function() {
        if (flash.parentNode) flash.parentNode.removeChild(flash);
      }, 400);
    }, 5000);
  }
});

/* --- Expiry Toggle (Tokens Page) --- */
function toggleExpiryInput() {
  var radio = document.querySelector('input[name="expiry_type"]:checked');
  var dateInput = document.getElementById('expiry-date');
  if (!radio || !dateInput) return;

  if (radio.value === 'custom') {
    dateInput.disabled = false;
    dateInput.required = true;
    dateInput.classList.remove('opacity-50', 'cursor-not-allowed');
  } else {
    dateInput.disabled = true;
    dateInput.required = false;
    dateInput.value = '';
    dateInput.classList.add('opacity-50', 'cursor-not-allowed');
  }
}

/* --- Row Click Navigation --- */
document.addEventListener('DOMContentLoaded', function() {
  var rows = document.querySelectorAll('tr.row-link');
  rows.forEach(function(row) {
    row.addEventListener('click', function(e) {
      if (e.target.closest('a, button, form')) return;
      var href = row.dataset.href;
      if (href) window.location.href = href;
    });
  });
});

/* --- Instance Checkbox Select All --- */
function toggleSelectAll(source) {
  var checkboxes = document.querySelectorAll('input[name="instance_access"]');
  checkboxes.forEach(function(cb) {
    cb.checked = source.checked;
    /* Trigger visual update for toggle-checkbox style */
    var evt = new Event('change', { bubbles: true });
    cb.dispatchEvent(evt);
  });
}

/* --- Auto-open Token Modal if new token exists --- */
document.addEventListener('DOMContentLoaded', function() {
  var tokenModal = document.getElementById('token-modal');
  if (tokenModal && tokenModal.dataset.autoOpen === 'true') {
    openModal('token-modal');
  }
});

/* --- Close sidebar on overlay click --- */
document.addEventListener('DOMContentLoaded', function() {
  var overlay = document.getElementById('sidebar-overlay');
  if (overlay) {
    overlay.addEventListener('click', toggleSidebar);
  }
});

/* --- Close modal on overlay click --- */
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-backdrop-blur') && e.target.classList.contains('active')) {
    e.target.classList.remove('active');
    document.body.style.overflow = '';
  }
});

/* --- Close modal on Escape key --- */
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    var modals = document.querySelectorAll('.modal-backdrop-blur.active');
    modals.forEach(function(m) {
      m.classList.remove('active');
    });
    document.body.style.overflow = '';
  }
});

/* --- Page enter animation --- */
document.addEventListener('DOMContentLoaded', function() {
  var content = document.getElementById('main-content');
  if (content) {
    content.classList.add('page-enter');
  }
});
