const viewDetails = {
  home:['Welcome to TRIO Tools', 'Choose a workflow to get started.'], announcement:['Weekly Canvas Announcement', 'Create a polished update, then copy the Canvas-ready HTML.'], logs:['Update logs from scratch', 'Launch the established Python automation when your browser tabs are ready.'], year:['Add a new school-year tab', 'Launch the established Python automation for a new school year.'], ids:['Student IDs', 'Edit the student IDs that the automation scripts use.']
};
const bannerUrl = 'https://lrccd.instructure.com/courses/83491/files/72721995/preview';
const instagramUrl = 'https://www.instagram.com/arc.triostem/';
const counselingUrl = 'https://sarsgrid.arc.losrios.edu/esars/thehubcounselstem/eSARS.asp?WCI=Init&amp;WCE=Settings';
const brookeUrl = 'https://sarsgrid.arc.losrios.edu/esars/TRIOSTEMStaff/eSARS.asp';
const announcementSections = [
  {id:'reminders', title:'Reminders', help:'Short, time-sensitive notes for students.', type:'reminder'},
  {id:'campus', title:'Campus News & Updates', help:'Campus announcements, deadlines, and events.', type:'article'},
  {id:'opportunities', title:'Student Opportunities & News', help:'Clubs, scholarships, programs, and other opportunities.', type:'article'},
  {id:'resources', title:'Student Resources', help:'Services and practical support for students.', type:'article'},
  {id:'handshake', title:'Handshake Events', help:'Career workshops, internships, and Handshake events.', type:'event'}
];
const ANNOUNCEMENT_DRAFT_KEY = 'trioTools.announcementDraft';
let restoringAnnouncementDraft = false;

function viewFromHash() {
  const view = window.location.hash.slice(1);
  return Object.hasOwn(viewDetails, view) ? view : 'home';
}

function showView(view, updateHash = true) {
  document.querySelectorAll('.page').forEach(page => page.classList.toggle('active', page.id === view));
  document.querySelectorAll('[data-view]').forEach(button => button.classList.toggle('active', button.dataset.view === view));
  document.getElementById('page-title').textContent = viewDetails[view][0];
  document.getElementById('page-subtitle').textContent = viewDetails[view][1];
  if (view === 'ids') loadIds();
  if (updateHash && window.location.hash !== `#${view}`) window.location.hash = view;
  window.scrollTo({top:0, behavior:'smooth'});
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
window.addEventListener('hashchange', () => showView(viewFromHash(), false));

async function api(path, payload = {}) {
  const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const data = await response.json().catch(() => ({error:'The tool returned an unexpected response.'}));
  if (!response.ok) throw data;
  return data;
}
function notice(id, message, type = '') { const el = document.getElementById(id); el.textContent = message; el.className = `notice ${type}`; }

document.getElementById('start-log').addEventListener('click', async () => {
  if (!confirm('Start the log update? Make sure the required browser tabs are open first.')) return;
  try { const data = await api('/api/start-log'); notice('log-notice', data.message, 'success'); } catch (error) { notice('log-notice', error.error || 'Could not start the update.', 'error'); }
});
document.getElementById('start-year').addEventListener('click', async () => {
  const year = document.getElementById('school-year').value.trim();
  if (!confirm(`Create ${year} tabs? Make sure the required browser tabs and sheet are open first.`)) return;
  try { const data = await api('/api/add-year', {year}); notice('year-notice', data.message, 'success'); } catch (error) { notice('year-notice', error.error || 'Could not start the school-year tool.', 'error'); }
});
async function loadIds() {
  try { const response = await fetch('/api/student-ids'); const data = await response.json(); document.getElementById('student-ids').value = data.student_ids.join('\n'); notice('ids-notice', ''); } catch { notice('ids-notice', 'Could not load the saved IDs.', 'error'); }
}
document.getElementById('reload-ids').addEventListener('click', loadIds);
document.getElementById('import-ids').addEventListener('click', () => document.getElementById('import-ids-file').click());
document.getElementById('import-ids-file').addEventListener('change', event => {
  const [file] = event.target.files;
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const contents = String(reader.result).replace(/^\uFEFF/, '');
    document.getElementById('student-ids').value = contents;
    const entries = contents.split(/\r?\n/).map(value => value.trim()).filter(Boolean);
    const invalid = entries.filter(value => !/^\d+$/.test(value));
    notice('ids-notice', invalid.length ? `Imported ${file.name}, but ${invalid.length} line${invalid.length === 1 ? '' : 's'} must be corrected before saving.` : `Imported ${entries.length} student IDs from ${file.name}. Review them, then select Save IDs.`, invalid.length ? 'error' : 'success');
  };
  reader.onerror = () => notice('ids-notice', `Could not read ${file.name}.`, 'error');
  reader.readAsText(file);
  event.target.value = '';
});
document.getElementById('save-ids').addEventListener('click', async () => {
  try { const data = await api('/api/student-ids', {student_ids:document.getElementById('student-ids').value}); notice('ids-notice', data.message, 'success'); } catch (error) { const lines = error.invalid_lines?.slice(0,5).map(line => `Line ${line.line}: ${line.value}`).join('; '); notice('ids-notice', `${error.error || 'Could not save IDs.'}${lines ? ` ${lines}` : ''}`, 'error'); }
});

function escapeHtml(value) { return value.trim().replace(/[&<>'"]/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;'}[char])); }
function safeUrl(value) { try { const url = new URL(value.trim()); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } }
function makeField(labelText, controlClass, placeholder, multiline = false) {
  const field = document.createElement('div'); field.className = 'field'; const id = `field-${Math.random().toString(36).slice(2)}`;
  field.innerHTML = `<label for="${id}">${labelText}</label>`; const control = document.createElement(multiline ? 'textarea' : 'input');
  control.id = id; control.className = controlClass; control.placeholder = placeholder; control.addEventListener('input', updateAnnouncement); field.append(control); return field;
}
function removeItemButton(item) { const button = document.createElement('button'); button.type = 'button'; button.className = 'danger'; button.textContent = 'Remove item'; button.addEventListener('click', () => { item.remove(); updateAnnouncement(); }); return button; }
function addAnnouncementItem(section, data = {}) {
  const item = document.createElement('div'); item.className = 'announcement-item'; const items = section.querySelector('.items');
  if (section.dataset.type === 'reminder') {
    const row = document.createElement('div'); row.className = 'inline-item'; const reminder = makeField('Reminder text', 'body-input', 'Add a reminder');
    reminder.querySelector('input').value = data.body || ''; row.append(reminder, removeItemButton(item)); item.append(row);
  } else {
    const headline = makeField(section.dataset.type === 'event' ? 'Event headline' : 'Content headline', 'headline-input', 'Give this item a title');
    const description = makeField('Description', 'body-input', 'Add a short description', true); const link = makeField('Link (optional)', 'url-input', 'https://...');
    headline.querySelector('input').value = data.title || ''; description.querySelector('textarea').value = data.body || ''; link.querySelector('input').value = data.url || '';
    item.append(headline, description, link, removeItemButton(item));
  }
  items.append(item); updateAnnouncement();
}
function buildAnnouncementSections() {
  const root = document.getElementById('announcement-sections');
  announcementSections.forEach(definition => {
    const section = document.createElement('div'); section.className = 'card announcement-section'; section.dataset.id = definition.id; section.dataset.type = definition.type;
    section.innerHTML = `<div class="section-top"><label class="section-check"><input type="checkbox" checked> ${definition.title}</label><button class="secondary" type="button">+ Add item</button></div><p class="section-help">${definition.help}</p><div class="items"></div>`;
    const toggle = section.querySelector('input'); toggle.addEventListener('change', () => { section.classList.toggle('disabled', !toggle.checked); updateAnnouncement(); }); section.querySelector('.secondary').addEventListener('click', () => addAnnouncementItem(section)); root.append(section);
  });
  addAnnouncementItem(document.querySelector('[data-id="reminders"]'));
}
function getItems(section) { return [...section.querySelectorAll('.announcement-item')].map(item => ({title:item.querySelector('.headline-input')?.value || '', body:item.querySelector('.body-input')?.value || '', url:item.querySelector('.url-input')?.value || ''})).filter(item => item.title.trim() || item.body.trim()); }
function saveAnnouncementDraft() {
  if (restoringAnnouncementDraft) return;
  const sections = Object.fromEntries(announcementSections.map(definition => {
    const section = document.querySelector(`[data-id="${definition.id}"]`);
    return [definition.id, {enabled: section.querySelector('input').checked, items: getItems(section)}];
  }));
  localStorage.setItem(ANNOUNCEMENT_DRAFT_KEY, JSON.stringify({week: document.getElementById('week').value, intro: document.getElementById('intro').value, sections}));
}
function restoreAnnouncementDraft() {
  let draft;
  try { draft = JSON.parse(localStorage.getItem(ANNOUNCEMENT_DRAFT_KEY)); } catch { return; }
  if (!draft || typeof draft !== 'object') return;
  if (typeof draft.week === 'string') document.getElementById('week').value = draft.week;
  if (typeof draft.intro === 'string') document.getElementById('intro').value = draft.intro;
  announcementSections.forEach(definition => {
    const saved = draft.sections?.[definition.id];
    if (!saved || !Array.isArray(saved.items)) return;
    const section = document.querySelector(`[data-id="${definition.id}"]`); const toggle = section.querySelector('input');
    toggle.checked = saved.enabled !== false; section.classList.toggle('disabled', !toggle.checked); section.querySelector('.items').replaceChildren();
    saved.items.forEach(item => addAnnouncementItem(section, item));
  });
}
function renderArticle(item, type) { const title = escapeHtml(item.title), body = escapeHtml(item.body), url = safeUrl(item.url); let html = '<div style="background-color: #F7FAFE; border: 1px solid #DCE4F0; border-radius: 8px; margin: 0 0 16px; padding: 18px;">'; if (title) html += `<h2 style="margin: 0 0 9px; color: #17355F; font-size: 24px; line-height: 1.3;">${title}</h2>`; if (body) html += `<p style="margin: 0; color: #24364B; font-size: 17px; line-height: 1.6;">${body}</p>`; if (url) html += `<p style="margin: 14px 0 0; font-size: 16px;"><a style="color: #1D4ED8; font-weight: bold;" href="${escapeHtml(url)}" target="_blank" rel="noopener">${type === 'event' ? 'View event details' : 'Learn more'} &rarr;</a></p>`; return html + '</div>'; }
function generateAnnouncementHtml() {
  const week = escapeHtml(document.getElementById('week').value), intro = escapeHtml(document.getElementById('intro').value);
  let html = `<div style="max-width: 760px; margin: 0 auto; font-family: Arial, Helvetica, sans-serif; color: #24364B; line-height: 1.55;">
<div style="margin: 0 0 18px; text-align: center;"><img style="display: block; width: 100%; max-width: 760px; height: auto; margin: 0 auto;" src="${bannerUrl}" alt="TRIO SSS STEM weekly newsletter"></div>
<p style="margin: 0 8px 18px; color: #24364B; font-size: 16px;"><strong>For more updates, follow our Instagram &rarr;</strong> <a style="color: #1D4ED8; font-weight: bold;" href="${instagramUrl}" target="_blank" rel="noopener">@arc.triostem</a></p>
<div style="margin: 0 0 18px; padding: 18px; background-color: #F7FAFE; border: 1px solid #DCE4F0; border-radius: 8px; text-align: center;"><h2 style="margin: 0 0 12px; color: #17355F; font-size: 24px; line-height: 1.3;">&#8902;.&#730;&#10022;&#730;.&#8902; Counseling Appointments &#8902;.&#730;&#10022;&#730;.&#8902;</h2><p style="margin: 0 0 8px; color: #24364B; font-size: 16px;">Make a Counseling Appointment Here &rarr; <a style="color: #1D4ED8; font-weight: bold;" href="${counselingUrl}" target="_blank" rel="noopener">Make Appointment Here</a></p><p style="margin: 0; color: #24364B; font-size: 16px;">Make an Appointment with Brooke Here &rarr; <a style="color: #1D4ED8; font-weight: bold;" href="${brookeUrl}" target="_blank" rel="noopener">Make Appointment With Brooke</a></p></div>`;
  if (week) html += `\n<p style="margin: 18px 8px 0; color: #52667F; font-size: 16px; text-align: center;"><strong>${week}</strong></p>`;
  if (intro) html += `\n<p style="margin: 24px 8px; color: #24364B; font-size: 17px; line-height: 1.6;">${intro}</p>`;
  announcementSections.forEach(definition => { const section = document.querySelector(`[data-id="${definition.id}"]`); if (!section.querySelector('input').checked) return; const items = getItems(section); if (!items.length) return; html += '\n<hr style="border: 0; border-top: 2px solid #DCE4F0; margin: 30px 0 18px;">'; html += definition.id === 'reminders' || definition.id === 'resources' ? `\n<h2 style="margin: 0 0 16px; color: #17355F; font-size: 24px; line-height: 1.35; text-align: center;">&#8902;.&#730;&#10022;&#730;.&#8902; ${definition.title} &#8902;.&#730;&#10022;&#730;.&#8902;</h2>` : `\n<h1 style="margin: 0 0 16px; color: #17355F; font-size: 30px; line-height: 1.2; text-align: center;">${definition.title}</h1>`; if (definition.type === 'reminder') { html += '\n<ul style="margin: 0; padding-left: 26px; color: #24364B; font-size: 17px;">'; items.forEach(item => html += `\n<li style="margin: 0 0 10px;">${escapeHtml(item.body)}</li>`); html += '\n</ul>'; } else { items.forEach(item => html += `\n${renderArticle(item, definition.type)}`); } });
  return html + '\n</div>';
}
function updateAnnouncement() { const html = generateAnnouncementHtml(); document.getElementById('generated-html').value = html; document.getElementById('canvas-preview').srcdoc = html; saveAnnouncementDraft(); }
document.getElementById('week').value = `Week of ${new Date().toLocaleDateString(undefined, {month:'long', day:'numeric', year:'numeric'})}`;
document.getElementById('intro').value = 'Here is what is happening this week. We hope these reminders and opportunities support your success!';
document.getElementById('week').addEventListener('input', updateAnnouncement); document.getElementById('intro').addEventListener('input', updateAnnouncement);
document.getElementById('copy-html').addEventListener('click', async () => { const html = generateAnnouncementHtml(); try { await navigator.clipboard.writeText(html); } catch { const output = document.getElementById('generated-html'); output.focus(); output.select(); document.execCommand('copy'); } const status = document.getElementById('copy-notice'); status.textContent = 'Copied! Paste the HTML into Canvas’s HTML editor.'; status.className = 'notice success'; setTimeout(() => { status.textContent = 'This is what students will see in Canvas.'; status.className = ''; }, 3000); });
restoringAnnouncementDraft = true;
buildAnnouncementSections();
restoreAnnouncementDraft();
restoringAnnouncementDraft = false;
updateAnnouncement();
showView(viewFromHash(), false);
