'use strict';
// ---------- State & helpers ----------
let TOKEN = localStorage.getItem('cc_token') || null;
let USER = null;
try { USER = JSON.parse(localStorage.getItem('cc_user') || 'null'); } catch { USER = null; }

function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function el(id){return document.getElementById(id);}
function toast(msg,type='info'){const c=el('toast-container');const t=document.createElement('div');t.className='toast '+type;t.textContent=msg;c.appendChild(t);setTimeout(()=>t.remove(),3200);}
function sbadge(s){const k=String(s||'').toLowerCase().replace(/[^a-z]/g,'');return `<span class="status ${k}">${esc(s)}</span>`;}

async function api(path,opts={}){
  const headers=opts.headers||{};
  if(TOKEN) headers['Authorization']='Bearer '+TOKEN;
  if(opts.body && !(opts.body instanceof FormData)){headers['Content-Type']='application/json';if(typeof opts.body!=='string')opts.body=JSON.stringify(opts.body);}
  let res;
  try{res=await fetch('/api'+path,{...opts,headers});}catch(e){toast('Network error','error');throw e;}
  if(res.status===401){logout();throw new Error('unauth');}
  let data=null;try{data=await res.json();}catch{data=null;}
  if(!res.ok){const msg=(data&&data.error)||('Error '+res.status);const err=new Error(msg);err.status=res.status;err.data=data;throw err;}
  return data;
}

// ---------- Auth ----------
function quickFill(email){el('login-email').value=email;el('login-password').value='password123';}
function toggleAuth(showReg){el('login-view').classList.toggle('hidden',showReg);el('register-view').classList.toggle('hidden',!showReg);}
async function doLogin(){
  const email=el('login-email').value.trim(),password=el('login-password').value;
  if(!email||!password){toast('Enter email and password','error');return;}
  try{const d=await api('/auth/login',{method:'POST',body:{email,password}});onAuth(d);}catch(e){toast(e.message||'Login failed','error');}
}
async function doRegister(){
  const body={name:el('reg-name').value.trim(),email:el('reg-email').value.trim(),password:el('reg-password').value,studentId:el('reg-studentId').value.trim(),department:el('reg-department').value.trim(),branch:el('reg-branch').value.trim(),section:el('reg-section').value.trim()};
  if(!body.name||!body.email||!body.password){toast('Name, email, password required','error');return;}
  try{const d=await api('/auth/register',{method:'POST',body});onAuth(d);toast('Account created','success');}catch(e){toast(e.message,'error');}
}
function onAuth(d){TOKEN=d.token;USER=d.user;localStorage.setItem('cc_token',TOKEN);localStorage.setItem('cc_user',JSON.stringify(USER));boot();}
function logout(){TOKEN=null;USER=null;localStorage.removeItem('cc_token');localStorage.removeItem('cc_user');el('app-screen').classList.add('hidden');el('auth-screen').classList.remove('hidden');}

// ---------- Navigation ----------
function isLead(){return USER&&USER.role==='ClubLead';}
function navItems(){
  const items=[['home','Home'],['clubs','Clubs'],['events','Events'],['my-registrations','My Registrations'],['my-club','My Club'],['notifications','Notifications']];
  if(isLead()) items.push(['control-panel','Control Panel']);
  return items;
}
function renderNav(active){
  el('main-nav').innerHTML=navItems().map(([k,l])=>`<a class="${k===active?'active':''}" onclick="go('${k}')">${l}</a>`).join('');
  el('user-chip').textContent=USER?`${USER.name} · ${USER.role}`:'';
}
function go(route){location.hash='#'+route;}
async function boot(){
  el('auth-screen').classList.add('hidden');el('app-screen').classList.remove('hidden');
  if(!location.hash)location.hash='#home';else router();
  loadUnread();
  if(!location.hash)router();else router();
}
window.addEventListener('hashchange',router);

async function loadUnread(){try{const d=await api('/notifications');const b=el('unread-badge');if(d.unreadCount>0){b.textContent=d.unreadCount;b.classList.remove('hidden');}else b.classList.add('hidden');}catch{}}

// ---------- Router ----------
function router(){
  const raw=(location.hash||'#home').slice(1);
  const [route,...rest]=raw.split('/');
  const arg=rest.join('/');
  const nav={'home':'home','clubs':'clubs','club':'clubs','events':'events','event':'events','my-registrations':'my-registrations','my-club':'my-club','notifications':'notifications','control-panel':'control-panel','cp':'control-panel'};
  renderNav(nav[route]||'home');
  const v=el('view');v.innerHTML='<div class="loading">Loading…</div>';
  const map={home:viewHome,clubs:viewClubs,club:viewClub,events:viewEvents,event:viewEvent,'my-registrations':viewMyRegistrations,'my-club':viewMyClub,notifications:viewNotifications,'control-panel':viewControlPanel,cp:viewControlPanel};
  (map[route]||viewHome)(v,arg).catch(e=>{if(e.message!=='unauth')v.innerHTML=`<div class="empty"><div class="big">⚠️</div>${esc(e.message||'Something went wrong')}</div>`;});
}

function head(title,sub){return `<div class="page-head"><h2>${esc(title)}</h2>${sub?`<p class="muted">${esc(sub)}</p>`:''}</div>`;}
function empty(icon,msg){return `<div class="glass empty"><div class="big">${icon}</div>${esc(msg)}</div>`;}

// ---------- Home ----------
async function viewHome(v){
  const [clubs,events]=await Promise.all([api('/clubs'),api('/events')]);
  v.innerHTML=`<div class="glass hero"><h2>Welcome back, ${esc((USER.name||'').split(' ')[0])} 👋</h2><p class="muted">Discover clubs, join communities and register for campus events — all in one place.</p></div>
  <div class="section-title">Clubs (${clubs.length})</div>
  <div class="grid cards">${clubs.slice(0,3).map(clubCard).join('')||empty('🏛️','No clubs yet')}</div>
  <div class="section-title">Upcoming Events (${events.length})</div>
  <div class="grid cards">${events.slice(0,3).map(eventCard).join('')||empty('📅','No events yet')}</div>`;
}

// ---------- Clubs ----------
function clubCard(c){return `<div class="glass card"><div class="row"><h3>${esc(c.name)}</h3><span class="tag">${esc(c.category||'')}</span></div>
  <div class="muted small">Club ID: ${esc(c.id)}</div>
  <p class="meta">${esc((c.description||'').slice(0,110))}${(c.description||'').length>110?'…':''}</p>
  <div class="meta"><b>Leader:</b> ${esc(c.clubLeader||'—')} &nbsp; <b>Faculty:</b> ${esc(c.facultyCoordinator||'—')}</div>
  <div class="stat"><span class="muted small"><b>${c.memberCount}</b> members</span><span class="muted small"><b>${c.projectCount}</b> projects</span><span class="muted small"><b>${c.eventCount}</b> events</span></div>
  <button class="btn btn-primary btn-sm" style="margin-top:12px" onclick="go('club/${c.id}')">View Club</button></div>`;}

async function viewClubs(v){const clubs=await api('/clubs');v.innerHTML=head('Clubs','Explore student clubs and communities on campus.')+`<div class="grid cards">${clubs.map(clubCard).join('')||empty('🏛️','No clubs available')}</div>`;}

async function viewClub(v,id){
  const [c,status]=await Promise.all([api('/clubs/'+id),api('/my/membership-status/'+id).catch(()=>({status:'Not Applied'}))]);
  let action='';
  if(status.status==='Approved')action=`<div>${sbadge('Approved')} <span class="muted">Member · ${esc(status.role||'')}</span></div>`;
  else if(status.status==='Pending')action=`<div>${sbadge('Pending')} <span class="muted">Request Pending</span></div>`;
  else if(status.status==='Rejected')action=`<div>${sbadge('Rejected')} <span class="muted">Application Rejected</span> <button class="btn btn-ghost btn-sm" onclick="joinModal(${c.id},'${esc(c.name)}')">Apply Again</button></div>`;
  else action=`<button class="btn btn-pink" onclick="joinModal(${c.id},'${esc(c.name)}')">Join Club</button>`;
  v.innerHTML=head(c.name,c.slogan||'')+`
  <div class="glass card"><div class="row"><span class="tag">${esc(c.category||'')}</span><span class="muted small">Club ID: ${esc(c.id)}</span></div>
  <p class="meta">${esc(c.description||'')}</p>
  <div class="meta"><b>Club Leader:</b> ${esc(c.clubLeader||'—')}<br><b>Faculty Coordinator:</b> ${esc(c.facultyCoordinator||'—')}<br><b>Campus:</b> ${esc(c.campus||'—')}</div>
  <div class="stat"><span class="muted small"><b>${c.memberCount}</b> members</span><span class="muted small"><b>${(c.projects||[]).length}</b> projects</span><span class="muted small"><b>${(c.events||[]).length}</b> events</span></div>
  <div style="margin-top:14px">${action}</div></div>
  <div class="section-title">Projects</div><div class="grid cards">${(c.projects||[]).map(projectCard).join('')||empty('📁','No projects yet')}</div>
  <div class="section-title">Events</div><div class="grid cards">${(c.events||[]).map(eventCard).join('')||empty('📅','No events yet')}</div>
  <div class="section-title">Updates</div><div class="grid">${(c.updates||[]).map(broadcastCard).join('')||empty('📢','No updates yet')}</div>`;
}

function projectCard(p){return `<div class="glass card"><div class="row"><h3>${esc(p.name)}</h3>${sbadge(p.status)}</div><p class="meta">${esc(p.description||'')}</p>${p.technologies?`<div class="meta"><b>Tech:</b> ${esc(p.technologies)}</div>`:''}${p.team?`<div class="meta"><b>Team:</b> ${esc(p.team)}</div>`:''}</div>`;}
function broadcastCard(b){return `<div class="glass card"><div class="row"><h3>${esc(b.title)}</h3><span class="tag">${esc(b.targetAudience||'')}</span></div><p class="meta">${esc(b.message||'')}</p><div class="muted small">${b.createdAt?new Date(b.createdAt).toLocaleString():''}</div></div>`;}

// Join modal
const ROLE_OPTIONS=['Technical','Operations','Marketing','Design','Corporate / Outreach','Finance','Event Management','Resource Management','Content','Other'];
function joinModal(clubId,name){
  const u=USER||{};
  openModal(`Join ${esc(name)}`,`
  <div class="form-grid">
    <div class="field"><label>Name</label><input id="j-name" value="${esc(u.name||'')}"></div>
    <div class="field"><label>Student ID</label><input id="j-sid" value="${esc(u.studentId||'')}"></div>
    <div class="field"><label>Email</label><input id="j-email" value="${esc(u.email||'')}"></div>
    <div class="field"><label>Department</label><input id="j-dept" value="${esc(u.department||'')}"></div>
    <div class="field"><label>Branch</label><input id="j-branch" value="${esc(u.branch||'')}"></div>
    <div class="field"><label>Section</label><input id="j-section" value="${esc(u.section||'')}"></div>
    <div class="field"><label>Year</label><input id="j-year" value="${esc(u.year||'')}"></div>
    <div class="field"><label>Requested Role</label><select id="j-role">${ROLE_OPTIONS.map(r=>`<option>${r}</option>`).join('')}</select></div>
    <div class="field full"><label>Skills</label><textarea id="j-skills"></textarea></div>
    <div class="field full"><label>Activities</label><textarea id="j-activities"></textarea></div>
    <div class="field full"><label>Projects</label><textarea id="j-projects"></textarea></div>
    <div class="field full"><label>Club-related Experience</label><textarea id="j-exp"></textarea></div>
    <div class="field full"><label>Contribution</label><textarea id="j-contrib"></textarea></div>
    <div class="field full"><label>Motivation</label><textarea id="j-motiv"></textarea></div>
  </div>`,`<button class="btn btn-primary" onclick="submitJoin(${clubId})">Submit Membership Request</button>`);
}
async function submitJoin(clubId){
  const body={requestedRole:el('j-role').value,skills:el('j-skills').value,activities:el('j-activities').value,projects:el('j-projects').value,clubRelatedExperience:el('j-exp').value,contribution:el('j-contrib').value,motivation:el('j-motiv').value};
  try{await api('/clubs/'+clubId+'/membership-requests',{method:'POST',body});closeModal();toast('Membership request submitted','success');router();loadUnread();}catch(e){toast(e.message,'error');}
}

// ---------- Events ----------
function eventCard(e){return `<div class="glass card"><div class="row"><h3>${esc(e.name)}</h3>${sbadge(e.status)}</div>
  <div class="muted small">${esc(e.eventId)} · ${esc(e.clubName||'')}</div>
  <p class="meta">${esc((e.description||'').slice(0,100))}</p>
  <div class="meta"><b>Date:</b> ${esc(e.eventDate||'—')} ${esc(e.startTime||'')} · <b>Venue:</b> ${esc(e.venue||'—')}</div>
  <div class="stat"><span class="muted small"><b>${e.availableCapacity}</b> seats left</span><span class="muted small">Deadline: ${esc(e.registrationDeadline||'—')}</span></div>
  <button class="btn btn-primary btn-sm" style="margin-top:12px" onclick="go('event/${encodeURIComponent(e.eventId)}')">View Event</button></div>`;}

async function viewEvents(v){const events=await api('/events');v.innerHTML=head('Events','Register for hackathons, workshops, seminars and more.')+`<div class="grid cards">${events.map(eventCard).join('')||empty('📅','No events available')}</div>`;}

async function viewEvent(v,id){
  const [e,st]=await Promise.all([api('/events/'+encodeURIComponent(id)),api('/events/'+encodeURIComponent(id)+'/registration-status').catch(()=>({registered:false}))]);
  const action=st.registered?`<div>${sbadge('Registered')} <span class="muted">✓ You are registered</span></div>`:`<button class="btn btn-pink" onclick="registerModal('${esc(e.eventId)}','${esc(e.name)}')">Register for Event</button>`;
  v.innerHTML=head(e.name,e.clubName||'')+`<div class="glass card"><div class="row"><span class="tag">${esc(e.category||'')}</span>${sbadge(e.status)}</div>
  <div class="muted small">Event ID: ${esc(e.eventId)}</div>
  <p class="meta">${esc(e.description||'')}</p>
  <div class="meta"><b>Date:</b> ${esc(e.eventDate||'—')}<br><b>Time:</b> ${esc(e.startTime||'')} – ${esc(e.endTime||'')}<br><b>Venue:</b> ${esc(e.venue||'—')}<br><b>Campus:</b> ${esc(e.campus||'—')}<br><b>Registration Deadline:</b> ${esc(e.registrationDeadline||'—')}</div>
  <div class="stat"><span class="muted small"><b>${e.registeredCount}</b> registered</span><span class="muted small"><b>${e.availableCapacity}</b> seats left</span></div>
  <div style="margin-top:14px">${action}</div></div>`;
}
function registerModal(eventId,name){const u=USER||{};openModal(`Register: ${esc(name)}`,`<div class="form-grid">
  <div class="field"><label>Name</label><input id="r-name" value="${esc(u.name||'')}"></div>
  <div class="field"><label>Student ID</label><input id="r-sid" value="${esc(u.studentId||'')}"></div>
  <div class="field"><label>Email</label><input id="r-email" value="${esc(u.email||'')}"></div>
  <div class="field"><label>Department</label><input id="r-dept" value="${esc(u.department||'')}"></div>
  <div class="field"><label>Branch</label><input id="r-branch" value="${esc(u.branch||'')}"></div>
  <div class="field"><label>Section</label><input id="r-section" value="${esc(u.section||'')}"></div>
  </div>`,`<button class="btn btn-primary" onclick="submitRegister('${esc(eventId)}')">Confirm Registration</button>`);}
async function submitRegister(eventId){const body={name:el('r-name').value,studentId:el('r-sid').value,email:el('r-email').value,department:el('r-dept').value,branch:el('r-branch').value,section:el('r-section').value};try{await api('/events/'+encodeURIComponent(eventId)+'/register',{method:'POST',body});closeModal();toast('Registered successfully','success');router();loadUnread();}catch(e){toast(e.message,'error');}}

// ---------- My Registrations ----------
async function viewMyRegistrations(v){const regs=await api('/my/registrations');v.innerHTML=head('My Registrations','Events you have registered for.')+(regs.length?`<div class="grid cards">${regs.map(r=>`<div class="glass card"><div class="row"><h3>${esc(r.event?r.event.name:r.eventId)}</h3>${sbadge('Registered')}</div><div class="muted small">${esc(r.eventId)}</div><div class="meta">${r.event?`<b>Date:</b> ${esc(r.event.eventDate||'—')} · <b>Venue:</b> ${esc(r.event.venue||'—')}`:''}</div><button class="btn btn-ghost btn-sm" style="margin-top:10px" onclick="go('event/${encodeURIComponent(r.eventId)}')">View</button></div>`).join('')}</div>`:empty('🎫','You have not registered for any events yet'));}

// ---------- My Club ----------
async function viewMyClub(v){
  const clubs=await api('/my/clubs');
  if(!clubs.length){v.innerHTML=head('My Club')+empty('🏛️','You are not an approved member of any club yet. Explore Clubs to join one!');return;}
  v.innerHTML=head('My Club','Your clubs, projects, updates and events.')+clubs.map(c=>`
  <div class="glass card"><div class="row"><h3>${esc(c.name)}</h3><span class="tag">${esc(c.myRole||'Member')}</span></div>
  <div class="muted small">${esc(c.slogan||'')}</div><p class="meta">${esc(c.description||'')}</p>
  <div class="meta"><b>Leader:</b> ${esc(c.clubLeader||'—')} · <b>Faculty:</b> ${esc(c.facultyCoordinator||'—')} · <b>Joined:</b> ${c.joinedAt?new Date(c.joinedAt).toLocaleDateString():'—'}</div></div>
  <div class="section-title">Projects</div><div class="grid cards">${(c.projects||[]).map(projectCard).join('')||empty('📁','No projects')}</div>
  <div class="section-title">Updates</div><div class="grid">${(c.updates||[]).map(broadcastCard).join('')||empty('📢','No updates')}</div>
  <div class="section-title">Events</div><div class="grid cards">${(c.events||[]).map(eventCard).join('')||empty('📅','No events')}</div>`).join('');
}

// ---------- Notifications ----------
async function viewNotifications(v){
  const d=await api('/notifications');
  v.innerHTML=head('Notifications',`${d.unreadCount} unread`)+`<div class="toolbar"><button class="btn btn-ghost btn-sm" onclick="markAllRead()">Mark all read</button></div>`+(d.notifications.length?`<div class="grid">${d.notifications.map(n=>`<div class="glass card" style="${n.isRead?'opacity:.65':''}"><div class="row"><h3>${esc(n.title)}</h3>${n.isRead?'':`<button class="btn btn-ghost btn-sm" onclick="markRead(${n.id})">Mark read</button>`}</div><p class="meta">${esc(n.message||'')}</p><div class="muted small">${n.createdAt?new Date(n.createdAt).toLocaleString():''}</div></div>`).join('')}</div>`:empty('🔔','No notifications'));
}
async function markRead(id){try{await api('/notifications/'+id+'/read',{method:'PUT'});router();loadUnread();}catch(e){toast(e.message,'error');}}
async function markAllRead(){try{await api('/notifications/read-all',{method:'PUT'});router();loadUnread();}catch(e){toast(e.message,'error');}}

// ---------- Control Panel (ClubLead) ----------
const CP_ITEMS=[['publish-event','📝','Publish New Event'],['broadcast','📢','Broadcast Message'],['requests','📥','Membership Requests'],['members','👥','Club Members'],['pub-events','📅','Published Events'],['reg-students','🎫','Registered Students'],['attendance','✅','Attendance'],['projects','📁','Club Projects'],['club-info','ℹ️','Club Information']];
let LED_CLUB=null;
async function ensureLedClub(){if(LED_CLUB)return LED_CLUB;const d=await api('/my/led-club');LED_CLUB=d.club;return LED_CLUB;}
async function viewControlPanel(v,sub){
  if(!isLead()){v.innerHTML=empty('🚫','403 Forbidden — Club Lead access only');return;}
  const club=await ensureLedClub();
  if(!club){v.innerHTML=empty('⚠️','You do not lead any club');return;}
  const parts=(sub||'').split('/');const panel=parts[0]||'';
  if(!panel){v.innerHTML=head('Control Panel',`Managing: ${club.name} (Club ID: ${club.id})`)+`<div class="grid hub">${CP_ITEMS.map(([k,i,l])=>`<div class="glass hub-item" onclick="go('control-panel/${k}')"><div class="ico">${i}</div><b>${l}</b></div>`).join('')}</div>`;return;}
  const back=`<button class="btn btn-ghost btn-sm" onclick="go('control-panel')">← Back to Control Panel</button>`;
  const fns={'publish-event':cpPublishEvent,'broadcast':cpBroadcast,'requests':cpRequests,'members':cpMembers,'pub-events':cpPubEvents,'reg-students':cpRegStudents,'attendance':cpAttendance,'projects':cpProjects,'club-info':cpClubInfo};
  const fn=fns[panel]||(async(v)=>{v.innerHTML=empty('❓','Unknown panel');});
  await fn(v,club,parts.slice(1).join('/'),back);
}

async function cpPublishEvent(v,club,_a,back){
  v.innerHTML=head('Publish New Event')+back+`<div class="glass card" style="margin-top:16px"><div class="form-grid">
    <div class="field"><label>Event ID *</label><input id="e-id" placeholder="AITC-HACK-004"></div>
    <div class="field"><label>Event Name *</label><input id="e-name"></div>
    <div class="field full"><label>Description</label><textarea id="e-desc"></textarea></div>
    <div class="field"><label>Event Date</label><input id="e-date" type="date"></div>
    <div class="field"><label>Category</label><input id="e-cat" placeholder="Hackathon"></div>
    <div class="field"><label>Start Time</label><input id="e-start" type="time"></div>
    <div class="field"><label>End Time</label><input id="e-end" type="time"></div>
    <div class="field"><label>Venue</label><input id="e-venue"></div>
    <div class="field"><label>Campus</label><input id="e-campus"></div>
    <div class="field"><label>Maximum Participants</label><input id="e-max" type="number" value="100"></div>
    <div class="field"><label>Registration Deadline</label><input id="e-deadline" type="date"></div>
  </div><div class="modal-actions"><button class="btn btn-primary" onclick="submitEvent()">Publish Event</button></div></div>`;
}
async function submitEvent(){const body={eventId:el('e-id').value.trim(),name:el('e-name').value.trim(),description:el('e-desc').value,eventDate:el('e-date').value,category:el('e-cat').value,startTime:el('e-start').value,endTime:el('e-end').value,venue:el('e-venue').value,campus:el('e-campus').value,maxParticipants:el('e-max').value,registrationDeadline:el('e-deadline').value};if(!body.eventId||!body.name){toast('Event ID and name required','error');return;}try{await api('/events',{method:'POST',body});toast('Event published','success');go('control-panel/pub-events');}catch(e){toast(e.message,'error');}}

async function cpBroadcast(v,club,_a,back){
  const AUD=['All Club Members',...ROLE_OPTIONS,'Event Participants'];
  v.innerHTML=head('Broadcast Message')+back+`<div class="glass card" style="margin-top:16px"><div class="form-grid">
    <div class="field"><label>Title *</label><input id="b-title"></div>
    <div class="field"><label>Target Audience</label><select id="b-aud">${AUD.map(a=>`<option>${a}</option>`).join('')}</select></div>
    <div class="field full"><label>Message</label><textarea id="b-msg"></textarea></div>
    <div class="field"><label>Publish Date</label><input id="b-pub" type="date"></div>
    <div class="field"><label>Expiry Date</label><input id="b-exp" type="date"></div>
  </div><div class="modal-actions"><button class="btn btn-primary" onclick="submitBroadcast(${club.id})">Send Broadcast</button></div></div>`;
}
async function submitBroadcast(clubId){const body={title:el('b-title').value.trim(),targetAudience:el('b-aud').value,message:el('b-msg').value,publishDate:el('b-pub').value,expiryDate:el('b-exp').value};if(!body.title){toast('Title required','error');return;}try{await api('/clubs/'+clubId+'/broadcasts',{method:'POST',body});toast('Broadcast sent','success');go('control-panel');}catch(e){toast(e.message,'error');}}

async function cpRequests(v,club,_a,back){
  const reqs=await api('/clubs/'+club.id+'/membership-requests');
  v.innerHTML=head('Membership Requests')+back+`<div style="margin-top:16px">${reqs.length?reqs.map(r=>`<div class="glass card" style="margin-bottom:14px"><div class="row"><h3>${esc(r.name)} · ${esc(r.requestedRole||'')}</h3>${sbadge(r.status)}</div>
  <div class="meta"><b>Student ID:</b> ${esc(r.studentId||'—')} · <b>Email:</b> ${esc(r.email||'—')}<br><b>Dept:</b> ${esc(r.department||'—')} · <b>Branch:</b> ${esc(r.branch||'—')} · <b>Section:</b> ${esc(r.section||'—')} · <b>Year:</b> ${esc(r.year||'—')}<br><b>Skills:</b> ${esc(r.skills||'—')}<br><b>Activities:</b> ${esc(r.activities||'—')}<br><b>Projects:</b> ${esc(r.projects||'—')}<br><b>Experience:</b> ${esc(r.clubRelatedExperience||'—')}<br><b>Contribution:</b> ${esc(r.contribution||'—')}<br><b>Motivation:</b> ${esc(r.motivation||'—')}<br><b>Submitted:</b> ${r.submittedAt?new Date(r.submittedAt).toLocaleString():'—'}</div>
  ${r.status==='Pending'?`<div class="modal-actions"><button class="btn btn-emerald btn-sm" onclick="reviewReq(${club.id},${r.id},'approve')">Approve</button><button class="btn btn-red btn-sm" onclick="reviewReq(${club.id},${r.id},'reject')">Reject</button></div>`:''}</div>`).join(''):empty('📥','No membership requests')}</div>`;
}
async function reviewReq(clubId,reqId,action){try{await api(`/clubs/${clubId}/membership-requests/${reqId}/${action}`,{method:'PUT',body:{}});toast('Request '+action+'d','success');router();}catch(e){toast(e.message,'error');}}

async function cpMembers(v,club,_a,back){
  const members=await api('/clubs/'+club.id+'/members');
  v.innerHTML=head('Club Members',`${members.length} members`)+back+`<div class="toolbar" style="margin-top:12px"><input id="m-search" placeholder="Search name…" oninput="filterMembers()"></div><div class="glass table-wrap"><table><thead><tr><th>Name</th><th>Student ID</th><th>Email</th><th>Dept</th><th>Role</th><th>Status</th><th>Joined</th></tr></thead><tbody id="m-body">${memberRows(members)}</tbody></table></div>`;
  window.__members=members;
}
function memberRows(ms){return ms.map(m=>`<tr><td>${esc(m.name||'')}</td><td>${esc(m.studentId||'')}</td><td>${esc(m.email||'')}</td><td>${esc(m.department||'')}</td><td>${esc(m.role||'')}</td><td>${sbadge(m.status)}</td><td>${m.joinedAt?new Date(m.joinedAt).toLocaleDateString():''}</td></tr>`).join('')||'<tr><td colspan=7 class="muted">No members</td></tr>';}
function filterMembers(){const q=el('m-search').value.toLowerCase();el('m-body').innerHTML=memberRows((window.__members||[]).filter(m=>(m.name||'').toLowerCase().includes(q)));}

async function cpPubEvents(v,club,_a,back){
  const events=(await api('/events')).filter(e=>e.clubId===club.id);
  v.innerHTML=head('Published Events',`${events.length} events`)+back+`<div class="grid cards" style="margin-top:16px">${events.length?events.map(e=>`<div class="glass card"><div class="row"><h3>${esc(e.name)}</h3>${sbadge(e.status)}</div><div class="muted small">${esc(e.eventId)}</div><div class="meta"><b>Date:</b> ${esc(e.eventDate||'—')} · <b>${e.registeredCount}</b> registered</div><div class="modal-actions"><button class="btn btn-ghost btn-sm" onclick="go('control-panel/reg-students/${encodeURIComponent(e.eventId)}')">Registered Students</button><button class="btn btn-ghost btn-sm" onclick="go('control-panel/attendance/${encodeURIComponent(e.eventId)}')">Attendance</button></div></div>`).join(''):empty('📅','No events published yet')}</div>`;
}

async function cpRegStudents(v,club,eventId,back){
  if(!eventId){const events=(await api('/events')).filter(e=>e.clubId===club.id);v.innerHTML=head('Registered Students','Select an event')+back+`<div class="grid cards" style="margin-top:16px">${events.map(e=>`<div class="glass card"><h3>${esc(e.name)}</h3><div class="muted small">${esc(e.eventId)} · ${e.registeredCount} registered</div><button class="btn btn-primary btn-sm" style="margin-top:10px" onclick="go('control-panel/reg-students/${encodeURIComponent(e.eventId)}')">View</button></div>`).join('')||empty('📅','No events')}</div>`;return;}
  const regs=await api('/events/'+encodeURIComponent(eventId)+'/registrations');
  v.innerHTML=head('Registered Students',`Event: ${eventId} · ${regs.length} registered`)+`<button class="btn btn-ghost btn-sm" onclick="go('control-panel/reg-students')">← All events</button><div class="glass table-wrap" style="margin-top:12px"><table><thead><tr><th>#</th><th>Name</th><th>Student ID</th><th>Email</th><th>Dept</th><th>Branch</th><th>Section</th><th>Registered</th></tr></thead><tbody>${regs.map((r,i)=>`<tr><td>${i+1}</td><td>${esc(r.name||'')}</td><td>${esc(r.studentId||'')}</td><td>${esc(r.email||'')}</td><td>${esc(r.department||'')}</td><td>${esc(r.branch||'')}</td><td>${esc(r.section||'')}</td><td>${r.registeredAt?new Date(r.registeredAt).toLocaleDateString():''}</td></tr>`).join('')||'<tr><td colspan=8 class="muted">No registrations</td></tr>'}</tbody></table></div>`;
}

async function cpAttendance(v,club,eventId,back){
  if(!eventId){const events=(await api('/events')).filter(e=>e.clubId===club.id);v.innerHTML=head('Attendance','Select an event')+back+`<div class="grid cards" style="margin-top:16px">${events.map(e=>`<div class="glass card"><h3>${esc(e.name)}</h3><div class="muted small">${esc(e.eventId)}</div><button class="btn btn-primary btn-sm" style="margin-top:10px" onclick="go('control-panel/attendance/${encodeURIComponent(e.eventId)}')">Mark Attendance</button></div>`).join('')||empty('📅','No events')}</div>`;return;}
  const rows=await api('/events/'+encodeURIComponent(eventId)+'/attendance');
  window.__att=rows.map(r=>({userId:r.userId,status:r.attendance}));
  v.innerHTML=head('Attendance',`Event: ${eventId}`)+`<button class="btn btn-ghost btn-sm" onclick="go('control-panel/attendance')">← All events</button><div class="glass table-wrap" style="margin-top:12px"><table><thead><tr><th>Name</th><th>Student ID</th><th>Status</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.name||'')}</td><td>${esc(r.studentId||'')}</td><td><select onchange="setAtt(${r.userId},this.value)">${['Not Marked','Present','Absent'].map(s=>`<option ${r.attendance===s?'selected':''}>${s}</option>`).join('')}</select></td></tr>`).join('')||'<tr><td colspan=3 class="muted">No registered students</td></tr>'}</tbody></table></div><div class="modal-actions"><button class="btn btn-primary" onclick="saveAtt('${esc(eventId)}')">Save Attendance</button></div>`;
}
function setAtt(uid,status){window.__att=window.__att||[];const f=window.__att.find(a=>a.userId===uid);if(f)f.status=status;else window.__att.push({userId:uid,status});}
async function saveAtt(eventId){try{await api('/events/'+encodeURIComponent(eventId)+'/attendance',{method:'PUT',body:{records:window.__att||[]}});toast('Attendance saved','success');}catch(e){toast(e.message,'error');}}

async function cpProjects(v,club,_a,back){
  const projects=await api('/clubs/'+club.id+'/projects');
  v.innerHTML=head('Club Projects')+back+`<div class="glass card" style="margin:16px 0"><h3 style="margin-bottom:10px">Add Project</h3><div class="form-grid"><div class="field"><label>Name *</label><input id="p-name"></div><div class="field"><label>Status</label><input id="p-status" value="Active"></div><div class="field full"><label>Description</label><textarea id="p-desc"></textarea></div><div class="field"><label>Technologies</label><input id="p-tech"></div><div class="field"><label>Team</label><input id="p-team"></div></div><div class="modal-actions"><button class="btn btn-primary" onclick="submitProject(${club.id})">Add Project</button></div></div><div class="grid cards">${projects.map(p=>`<div class="glass card"><div class="row"><h3>${esc(p.name)}</h3>${sbadge(p.status)}</div><p class="meta">${esc(p.description||'')}</p>${p.technologies?`<div class="meta"><b>Tech:</b> ${esc(p.technologies)}</div>`:''}<button class="btn btn-red btn-sm" style="margin-top:10px" onclick="delProject(${club.id},${p.id})">Delete</button></div>`).join('')||empty('📁','No projects yet')}</div>`;
}
async function submitProject(clubId){const body={name:el('p-name').value.trim(),status:el('p-status').value,description:el('p-desc').value,technologies:el('p-tech').value,team:el('p-team').value};if(!body.name){toast('Name required','error');return;}try{await api('/clubs/'+clubId+'/projects',{method:'POST',body});toast('Project added','success');router();}catch(e){toast(e.message,'error');}}
async function delProject(clubId,pid){if(!confirm('Delete this project?'))return;try{await api('/clubs/'+clubId+'/projects/'+pid,{method:'DELETE'});toast('Deleted','success');router();}catch(e){toast(e.message,'error');}}

async function cpClubInfo(v,club,_a,back){
  const c=await api('/clubs/'+club.id);
  v.innerHTML=head('Club Information')+back+`<div class="glass card" style="margin-top:16px"><h3>${esc(c.name)}</h3><div class="muted small">Club ID: ${esc(c.id)}</div><p class="meta">${esc(c.description||'')}</p><div class="meta"><b>Slogan:</b> ${esc(c.slogan||'—')}<br><b>Category:</b> ${esc(c.category||'—')}<br><b>Campus:</b> ${esc(c.campus||'—')}<br><b>Leader:</b> ${esc(c.clubLeader||'—')}<br><b>Faculty Coordinator:</b> ${esc(c.facultyCoordinator||'—')}</div><div class="stat"><span class="muted small"><b>${c.memberCount}</b> members</span><span class="muted small"><b>${(c.projects||[]).length}</b> projects</span><span class="muted small"><b>${(c.events||[]).length}</b> events</span></div></div>`;
}

// ---------- Modal ----------
function openModal(title,body,actions){el('modal-root').innerHTML=`<div class="modal-overlay" onclick="if(event.target===this)closeModal()"><div class="glass modal"><h2>${title}</h2>${body}<div class="modal-actions"><button class="btn btn-ghost" onclick="closeModal()">Cancel</button>${actions||''}</div></div></div>`;}
function closeModal(){el('modal-root').innerHTML='';}

// ---------- Init ----------
if(TOKEN&&USER){boot();}else{el('auth-screen').classList.remove('hidden');}
window.doLogin=doLogin;window.doRegister=doRegister;window.toggleAuth=toggleAuth;window.quickFill=quickFill;window.logout=logout;window.go=go;
