/* COLLEGE_FANTASY_DEMO_FORCE_CLEAN_V2
   One-time demo reset. Runs before the application reads saved browser state.
   After the first clean load, new user actions may persist normally according
   to the app's save/submit behavior.
*/
(() => {
  const RESET_KEY = 'college_fantasy_demo_force_clean_v2_done';
  try {
    if (localStorage.getItem(RESET_KEY) !== '1') {
      localStorage.clear();
      sessionStorage.clear();
      localStorage.setItem(RESET_KEY, '1');
    }
  } catch (err) {
    console.warn('Demo clean-start reset could not access browser storage.', err);
  }
})();

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const clamp = (n,a,b) => Math.max(a, Math.min(b,n));
const money = n => `${Number(n||0).toFixed(1)}M`;
const worldOrder = ['D1','D2','NAIA','NJCAA1'];
const DAILY_GUESS_ROUNDS = 5;
const worlds = {
  D1:{label:'NCAA D1',budget:120,source:'https://www.ncaa.com/sports/soccer-men/d1'},
  D2:{label:'NCAA D2',budget:120,source:'https://www.ncaa.com/sports/soccer-men/d2'},
  D3:{label:'NCAA D3',budget:120,source:'https://www.ncaa.com/sports/soccer-men/d3'},
  NAIA:{label:'NAIA',budget:120,source:'https://www.naia.org/sports/mens-soccer/'},
  NJCAA1:{label:'NJCAA D1',budget:120,source:'https://www.njcaa.org/sports/msoc/index'}
};
const formations = {
 '4-3-3':{GK:1,DF:4,MF:3,FW:3}, '4-4-2':{GK:1,DF:4,MF:4,FW:2},
 '3-5-2':{GK:1,DF:3,MF:5,FW:2}, '3-4-3':{GK:1,DF:3,MF:4,FW:3}
};
const conferenceStrength = {'ACC':1,'Big Ten':.98,'SEC':.96,'Big 12':.94,'Big East':.92,'Pac-12':.92,'American Athletic':.84,'ASUN':.74,'Big West':.81,'CUSA':.77,'A-10':.78,'Summit League':.70,'Sun Belt':.82,'GLIAC':.79,'PSAC':.76,'NE10':.75,'CCAA':.79,'SCIAC':.68,'NESCAC':.78,'UAA':.80,'Crossroads':.75,'GSAC':.76,'Sun Conference':.74,'Kansas Jayhawk':.72,'Region 8':.72,'Region 14':.70};
const i18n = {
 en:{dashboard:'Dashboard',lineup:'Lineup',market:'Market',budgetBoost:'Budget Boost',rankings:'Rankings',competitions:'Competitions',dailyGames:'Daily Games',seasonProgress:'2026 season in progress.',syncCopy:'Scores, rankings and news can sync with public sources.',gamesPredictions:'GAMES & PREDICTIONS',viewProfile:'VIEW PROFILE',latestRound:'World participation',worldNote:'Each world is independent. Play only the ones you want.',quickAccess:'Quick Access',allWorlds:'All worlds. One profile.',worldBanner:'Build lineups, manage budgets, track rankings and compete across every world.',exploreWorlds:'EXPLORE WORLDS',collegeSoccer:'COLLEGE SOCCER',newsTitle:'College Soccer News',refresh:'Refresh',openNcaa:'OPEN NCAA ↗',all:'All',roundPredictions:'Game Predictions',predictCopy:'Browse every available game and predict only the matches you want.',browseAllGames:'BROWSE ALL GAMES',savePredictions:'SAVE PREDICTIONS',results:'RESULTS',realScores:'Live & latest scores',viewAllResults:'VIEW ALL RESULTS',buildTeam:'Build your team',worldsIndependent:'Independent worlds — participate only in the ones you want.',formation:'Formation',baseBudget:'Budget base',playersSelected:'Players (0/11)',remaining:'Remaining',avgPlayer:'Avg. per player',howScoring:'HOW SCORING WORKS',confirmLineup:'CONFIRM LINEUP',lineupOnPitch:'Lineup on the pitch',changeStadium:'Change stadium view',yourXi:'YOUR XI',yourLineup:'Your Lineup',benchOptional:'BENCH (OPTIONAL)',openMarket:'OPEN MARKET',marketTitle:'Player Market',marketDesc:'Real players and coaches with fantasy prices driven by individual production, team strength, conference level and role.',availableBudget:'Available budget',players:'Players',headCoach:'Head Coach',assistantCoach:'Assistant Coach',allPositions:'All positions',allConferences:'All conferences',allSchools:'All schools',allClasses:'All classes',priceHigh:'Price: high to low',priceLow:'Price: low to high',minutesHigh:'Minutes: high to low',searchPlayers:'Search players...',syncData:'SYNC DATA',howCalculate:'How we calculate it',buyBudgetBoost:'GET BUDGET BOOST',clearFilters:'Clear filters',boostDesc:'Optional fantasy budget benefits. This prototype activates them locally and never processes payment.',currentBoost:'Your boost',thisWorldOnly:'valid in this world',rankingsDesc:'National rankings, conference tables, scoring leaders, assist leaders and defensive performance across every world.',nationalRanking:'National ranking',conferenceStandings:'Conference standings',topScorers:'Top scorers',assistLeaders:'Assist leaders',bestDefenses:'Best defenses',cleanSheetLeaders:'Clean-sheet leaders',competitionsDesc:'Your private and public fantasy leagues. You never have to play every world.',games:'Games & Results',gamesDesc:'Choose a date, conference and school to browse every game in the active world.',selectDate:'Select date',allStatuses:'All games',liveOnly:'Live',scheduledOnly:'Scheduled',finalOnly:'Final',gamesOn:'Games on',calendar:'Calendar',predShowing:'Showing',ofGames:'games',loginHeadline:'College soccer. One fantasy game.',loginSub:'NCAA D1, NCAA D2, NAIA and NJCAA D1 in separate worlds.',password:'Password',enter:'Enter',loginLegal:'Prototype: no real payment is processed.'},
 pt:{dashboard:'Dashboard',lineup:'Escalação',market:'Mercado',budgetBoost:'Budget Boost',rankings:'Rankings',competitions:'Competições',dailyGames:'Jogos Diários',seasonProgress:'Temporada 2026 em andamento.',syncCopy:'Resultados, rankings e notícias podem sincronizar com fontes públicas.',gamesPredictions:'JOGOS & PALPITES',viewProfile:'VER PERFIL',latestRound:'Participação nos mundos',worldNote:'Cada mundo é independente. Jogue apenas os que quiser.',quickAccess:'Acesso rápido',allWorlds:'Todos os mundos. Um perfil.',worldBanner:'Monte escalações, gerencie orçamentos, acompanhe rankings e compita em cada mundo.',exploreWorlds:'EXPLORAR MUNDOS',collegeSoccer:'COLLEGE SOCCER',newsTitle:'Notícias do College Soccer',refresh:'Atualizar',openNcaa:'ABRIR NCAA ↗',all:'Todos',roundPredictions:'Palpites de jogos',predictCopy:'Veja todos os jogos disponíveis e palpite apenas nos que quiser.',browseAllGames:'VER TODOS OS JOGOS',savePredictions:'SALVAR PALPITES',results:'RESULTADOS',realScores:'Resultados ao vivo e recentes',viewAllResults:'VER TODOS OS RESULTADOS',buildTeam:'Monte seu time',worldsIndependent:'Mundos independentes — participe apenas dos que quiser.',formation:'Formação',baseBudget:'Orçamento base',playersSelected:'Jogadores (0/11)',remaining:'Restante',avgPlayer:'Média por jogador',howScoring:'COMO PONTUA?',confirmLineup:'CONFIRMAR ESCALAÇÃO',lineupOnPitch:'Escalação no campo',changeStadium:'Alterar vista do estádio',yourXi:'SEU XI',yourLineup:'Sua Escalação',benchOptional:'BANCO (OPCIONAL)',openMarket:'ABRIR MERCADO',marketTitle:'Mercado de Jogadores',marketDesc:'Jogadores e treinadores com preços fantasy guiados por produção individual, força do time, nível da conferência e função.',availableBudget:'Orçamento disponível',players:'Jogadores',headCoach:'Head Coach',assistantCoach:'Assistant Coach',allPositions:'Todas posições',allConferences:'Todas conferências',allSchools:'Todas escolas',allClasses:'Todas classes',priceHigh:'Preço: maior para menor',priceLow:'Preço: menor para maior',minutesHigh:'Minutos: maior para menor',searchPlayers:'Buscar jogadores...',syncData:'SINCRONIZAR',howCalculate:'Como calculamos',buyBudgetBoost:'OBTER BUDGET BOOST',clearFilters:'Limpar filtros',boostDesc:'Benefícios opcionais de orçamento fantasy. Este protótipo ativa localmente e não processa pagamento.',currentBoost:'Seu boost',thisWorldOnly:'válido neste mundo',rankingsDesc:'Rankings nacionais, tabelas de conferência, artilharia, assistências e desempenho defensivo de todos os mundos.',nationalRanking:'Ranking nacional',conferenceStandings:'Classificação por conferência',topScorers:'Artilharia',assistLeaders:'Assistências',bestDefenses:'Melhores defesas',cleanSheetLeaders:'Clean sheets',competitionsDesc:'Suas ligas fantasy públicas e privadas. Você não precisa jogar em todos os mundos.',games:'Jogos & Resultados',gamesDesc:'Escolha uma data, conferência e faculdade para ver todos os jogos do mundo ativo.',selectDate:'Selecionar data',allStatuses:'Todos os jogos',liveOnly:'Ao vivo',scheduledOnly:'Agendados',finalOnly:'Encerrados',gamesOn:'Jogos em',calendar:'Calendário',predShowing:'Mostrando',ofGames:'jogos',loginHeadline:'College soccer. Um fantasy game.',loginSub:'NCAA D1, NCAA D2, NAIA e NJCAA D1 em mundos separados.',password:'Senha',enter:'Entrar',loginLegal:'Protótipo: nenhum pagamento real é processado.'},
 es:{dashboard:'Dashboard',lineup:'Alineación',market:'Mercado',budgetBoost:'Budget Boost',rankings:'Rankings',competitions:'Competiciones',dailyGames:'Juegos Diarios',seasonProgress:'Temporada 2026 en curso.',syncCopy:'Resultados, rankings y noticias pueden sincronizarse con fuentes públicas.',gamesPredictions:'PARTIDOS & PRONÓSTICOS',viewProfile:'VER PERFIL',latestRound:'Participación en mundos',worldNote:'Cada mundo es independiente. Juega solo los que quieras.',quickAccess:'Acceso rápido',allWorlds:'Todos los mundos. Un perfil.',worldBanner:'Crea alineaciones, gestiona presupuestos, sigue rankings y compite en cada mundo.',exploreWorlds:'EXPLORAR MUNDOS',collegeSoccer:'COLLEGE SOCCER',newsTitle:'Noticias de College Soccer',refresh:'Actualizar',openNcaa:'ABRIR NCAA ↗',all:'Todos',roundPredictions:'Pronósticos',predictCopy:'Mira todos los partidos disponibles y pronostica solo los que quieras.',browseAllGames:'VER TODOS LOS PARTIDOS',savePredictions:'GUARDAR PRONÓSTICOS',results:'RESULTADOS',realScores:'Resultados en vivo y recientes',viewAllResults:'VER TODOS LOS RESULTADOS',buildTeam:'Arma tu equipo',worldsIndependent:'Mundos independientes — participa solo en los que quieras.',formation:'Formación',baseBudget:'Presupuesto base',playersSelected:'Jugadores (0/11)',remaining:'Restante',avgPlayer:'Promedio por jugador',howScoring:'CÓMO PUNTÚA',confirmLineup:'CONFIRMAR ALINEACIÓN',lineupOnPitch:'Alineación en el campo',changeStadium:'Cambiar vista del estadio',yourXi:'TU XI',yourLineup:'Tu Alineación',benchOptional:'BANQUILLO (OPCIONAL)',openMarket:'ABRIR MERCADO',marketTitle:'Mercado de Jugadores',marketDesc:'Jugadores y entrenadores con precios fantasy basados en producción individual, fuerza del equipo, nivel de conferencia y rol.',availableBudget:'Presupuesto disponible',players:'Jugadores',headCoach:'Head Coach',assistantCoach:'Assistant Coach',allPositions:'Todas posiciones',allConferences:'Todas conferencias',allSchools:'Todas escuelas',allClasses:'Todas clases',priceHigh:'Precio: mayor a menor',priceLow:'Precio: menor a mayor',minutesHigh:'Minutos: mayor a menor',searchPlayers:'Buscar jugadores...',syncData:'SINCRONIZAR',howCalculate:'Cómo calculamos',buyBudgetBoost:'OBTENER BUDGET BOOST',clearFilters:'Limpiar filtros',boostDesc:'Beneficios opcionales de presupuesto fantasy. Este prototipo los activa localmente y no procesa pagos.',currentBoost:'Tu boost',thisWorldOnly:'válido en este mundo',rankingsDesc:'Rankings nacionales, tablas de conferencia, goleadores, asistencias y rendimiento defensivo de todos los mundos.',nationalRanking:'Ranking nacional',conferenceStandings:'Clasificación por conferencia',topScorers:'Goleadores',assistLeaders:'Asistencias',bestDefenses:'Mejores defensas',cleanSheetLeaders:'Clean sheets',competitionsDesc:'Tus ligas fantasy públicas y privadas. No necesitas jugar en todos los mundos.',games:'Partidos & Resultados',gamesDesc:'Elige una fecha, conferencia y universidad para ver todos los partidos del mundo activo.',selectDate:'Seleccionar fecha',allStatuses:'Todos los partidos',liveOnly:'En vivo',scheduledOnly:'Programados',finalOnly:'Finalizados',gamesOn:'Partidos del',calendar:'Calendario',predShowing:'Mostrando',ofGames:'partidos',loginHeadline:'College soccer. Un fantasy game.',loginSub:'NCAA D1, NCAA D2, NAIA y NJCAA D1 en mundos separados.',password:'Contraseña',enter:'Entrar',loginLegal:'Prototipo: no se procesa ningún pago real.'}
};

const verifiedRankingSnapshots={};
// Official NCAA.com scoreboard snapshot packaged for the delivery date.  It is
// only used when the browser date matches this snapshot; live/cache refreshes
// merge over it automatically.
const verifiedGameSnapshots={
 D1:{'2026-09-23':[
  {game_date:'2026-09-23',home_team:'Massachusetts',away_team:'FDU',status:'scheduled · 3:00 PM EDT',division:'D1',start_time:'3:00 PM EDT',source_name:'NCAA.com',source_url:'https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf'},
  {game_date:'2026-09-23',home_team:'Sacramento St.',away_team:'UC Riverside',status:'scheduled · 4:00 PM EDT',division:'D1',start_time:'4:00 PM EDT',source_name:'NCAA.com',source_url:'https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf'},
  {game_date:'2026-09-23',home_team:'Georgia St.',away_team:'UNC Asheville',status:'scheduled · 6:00 PM EDT',division:'D1',start_time:'6:00 PM EDT',source_name:'NCAA.com',source_url:'https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf'},
  {game_date:'2026-09-23',home_team:'Holy Cross',away_team:'Stonehill',status:'scheduled · 6:00 PM EDT',division:'D1',start_time:'6:00 PM EDT',source_name:'NCAA.com',source_url:'https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf'},
  {game_date:'2026-09-23',home_team:'UAB',away_team:'Gardner-Webb',status:'scheduled · 7:00 PM EDT',division:'D1',start_time:'7:00 PM EDT',source_name:'NCAA.com',source_url:'https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf'},
  {game_date:'2026-09-23',home_team:'Radford',away_team:'VMI',status:'scheduled · 7:00 PM EDT',division:'D1',start_time:'7:00 PM EDT',source_name:'NCAA.com',source_url:'https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf'},
  {game_date:'2026-09-23',home_team:'UC San Diego',away_team:'Cal St. Fullerton',status:'scheduled · 10:00 PM EDT',division:'D1',start_time:'10:00 PM EDT',source_name:'NCAA.com',source_url:'https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf'},
  {game_date:'2026-09-23',home_team:'Oregon St.',away_team:'Seattle U',status:'scheduled · 10:00 PM EDT',division:'D1',start_time:'10:00 PM EDT',source_name:'NCAA.com',source_url:'https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf'}
 ]}
};
// One-time clean start for the published demo. This is NOT a user-facing reset.
const DEMO_RESET_VERSION='demo-clean-2026-09-25-v1';
if(localStorage.getItem('college_fantasy_demo_reset_version')!==DEMO_RESET_VERSION){
  Object.keys(localStorage)
    .filter(k=>k.startsWith('college_fantasy_'))
    .forEach(k=>localStorage.removeItem(k));

  Object.keys(sessionStorage)
    .filter(k=>k.startsWith('college_fantasy_') && k!=='college_fantasy_v1_authenticated')
    .forEach(k=>sessionStorage.removeItem(k));

  localStorage.setItem('college_fantasy_demo_reset_version',DEMO_RESET_VERSION);
}

const saved=JSON.parse(localStorage.getItem('college_fantasy_v1_state')||'{}');
const state={lang:saved.lang||'en',activeWorld:saved.activeWorld||'D1',profile:saved.profile||{team:'Campus Eleven F.C.',handle:'manager',initials:'LC'},participation:saved.participation||{D1:true,D2:false,D3:false,NAIA:false,NJCAA1:false},worldState:saved.worldState||{},predictions:saved.predictions||{},dailyGames:saved.dailyGames||{},leagues:saved.leagues||[],dashboardCache:saved.dashboardCache||{},players:[],coaches:[],games:[],news:[],filters:{conferences:[],schools:[]},teamRows:[],gameCoverage:null,statsCoverage:null,statsSyncing:{},rankingWorld:saved.rankingWorld||'D1',rankingCat:saved.rankingCat||'scorers',rankingPage:1,rankingPageSize:15,rankingConferences:{},rankingSyncing:false,gameFilter:'all',gameConference:'all',gameSchool:'all',gameDate:saved.gameDate||isoToday(),predConference:'all',predSchool:'all',predPage:1,predPageSize:15,newsFilter:'all',rankingRemote:{},rankingLoading:{},seasonSyncing:{},refreshTimersStarted:false,marketVisibleCount:60,marketContext:{type:'players',position:'all',bench:false},rosterLoaded:false,rosterPromise:null,playerBuckets:{},coachesLoaded:false,coachPromise:null,marketLoading:false,filtersLoaded:false,extendedGamesLoaded:false,coverageLoaded:false,loadToken:0};
state.dailyPickemDate=isoToday();state.dailyPickemMode='today';state.dailyPickemCache={};state.dailyPickemLoading=false;state.dailyGuessRound=1;state.dailyGuessRuntime=null;state.dailyGuessLoading=false;state.dailyGuessSelected=null;state.dailyGuessSearchTimer=null;
// One-time reset for the Pedro Arcoverde QA test: make NCAA D1 Player 1 start fresh.
const PEDRO_TEST_RESET_KEY='college_fantasy_pedro_test_2026-09-25_v4';
if(!localStorage.getItem(PEDRO_TEST_RESET_KEY)){
 const d1=state.dailyGames?.D1;
 if(d1?.guessByDate){delete d1.guessByDate['2026-09-25#1'];}
 state.dailyGuessRound=1;
 state.dailyGuessRuntime=null;
 state.dailyGuessSelected=null;
 localStorage.setItem(PEDRO_TEST_RESET_KEY,'1');
}
function save(){localStorage.setItem('college_fantasy_v1_state',JSON.stringify({lang:state.lang,activeWorld:state.activeWorld,profile:state.profile,participation:state.participation,worldState:state.worldState,predictions:state.predictions,dailyGames:state.dailyGames,leagues:state.leagues,dashboardCache:state.dashboardCache,rankingWorld:state.rankingWorld,rankingCat:state.rankingCat,gameDate:state.gameDate}))}
function cacheDashboardWorld(world=state.activeWorld){if(world!==state.activeWorld)return;state.dashboardCache[world]={news:(state.news||[]).slice(0,12),games:(state.games||[]).filter(g=>g.game_date>=isoOffset(-1)&&g.game_date<=isoOffset(10)).slice(0,220),prospects:(state.prospects||[]).slice(0,8),cached_at:new Date().toISOString()};save()}
function tr(k){return i18n[state.lang]?.[k]||i18n.en[k]||k}
function ws(world=state.activeWorld){if(!state.worldState[world])state.worldState[world]={formation:'4-3-3',boost:0,lineup:{starters:[],bench:{},HC:null,AC:null},seeded:false};return state.worldState[world]}
function baseBudget(world=state.activeWorld){return worlds[world].budget}
function totalBudget(world=state.activeWorld){return baseBudget(world)+(ws(world).boost||0)}
function selectedPlayerIds(world=state.activeWorld){const l=ws(world).lineup;return [...l.starters,...Object.values(l.bench||{}).filter(Boolean)]}
function spent(world=state.activeWorld){if(world!==state.activeWorld)return 0;const data=state.players;const coaches=state.coaches;const l=ws(world).lineup;const ids=new Set(selectedPlayerIds(world));let total=data.filter(p=>ids.has(p.id)).reduce((sum,p)=>sum+Number(p.price||0),0);[l.HC,l.AC].filter(Boolean).forEach(id=>{const c=coaches.find(x=>x.id===id);if(c)total+=Number(c.price||0)});return total}
function available(world=state.activeWorld){return totalBudget(world)-spent(world)}
function displayOverall(p){const stored=Number(p.rating);if(Number.isFinite(stored)&&stored>=75)return clamp(Math.round(stored),75,99);const price=Number(p.price||5);return clamp(Math.round(75+((price-5)/11)*24),75,99)}
function normalizePosition(p){const x=(p||'').toUpperCase();if(x.startsWith('G'))return'GK';if(x.startsWith('D'))return'DF';if(x.startsWith('M'))return'MF';return'FW'}
function classNorm(x){const v=(x||'').toLowerCase();if(v.includes('fr'))return'Freshman';if(v.includes('so'))return'Sophomore';if(v.includes('jr'))return'Junior';if(v.includes('sr'))return'Senior';if(v.includes('gr')||v.includes('5'))return'Graduate';return x||'Junior'}
function numOrNull(v){return v===null||v===undefined||v===''?null:Number(v)}
function normalizeApiPlayer(p){const verified=Boolean(p.source_url&&p.source_name&&!String(p.source_name).toLowerCase().includes('prototype'));const statsVerified=Boolean(p.stats_source_url&&p.stats_source_name&&!String(p.stats_source_name).toLowerCase().includes('prototype'));const hasStats=statsVerified;const metric=v=>statsVerified?numOrNull(v):null;return {...p,id:`API-${p.id}`,position:normalizePosition(p.position),class_year:classNorm(p.class_year),rating:displayOverall(p),price:Number(p.price||5),minutes:metric(p.minutes),goals:metric(p.goals),assists:metric(p.assists),shutouts:metric(p.shutouts),games:metric(p.games),saves:metric(p.saves),avatar:null,verified,hasStats}}
async function jfetch(url,fallback,timeout=3500){const c=new AbortController();const t=setTimeout(()=>c.abort(),timeout);try{const r=await fetch(url,{signal:c.signal});if(!r.ok)throw new Error('bad response');return await r.json()}catch(e){return fallback}finally{clearTimeout(t)}}
function query(path,obj={}){if(location.protocol==='file:'||location.origin==='null')return path;const u=new URL(path,location.origin);Object.entries(obj).forEach(([k,v])=>u.searchParams.set(k,v));return u.pathname+u.search}

const fallbackNews={D1:[],NJCAA1:[]};
function boot(show=true){const el=$('#bootOverlay');if(el)el.classList.toggle('hidden',!show)}

function buildNav(){const items=[['dashboard','dashboard'],['team','lineup'],['rankings','rankings'],['competitions','competitions'],['games','games'],['daily-games','dailyGames']];$('#nav').innerHTML=items.map(([id,k])=>`<button class="nav-tab" data-jump="${id}">${tr(k)}</button>`).join('')}
function applyLang(){document.documentElement.lang=state.lang;$$('[data-i18n]').forEach(el=>el.textContent=tr(el.dataset.i18n));$$('[data-i18n-placeholder]').forEach(el=>el.placeholder=tr(el.dataset.i18nPlaceholder));$$('[data-lang]').forEach(b=>b.classList.toggle('active',b.dataset.lang===state.lang));$$('[data-login-lang]').forEach(b=>b.classList.toggle('active',b.dataset.loginLang===state.lang));buildNav();markActiveNav()}
function markActiveNav(){let active=$('.page.active')?.id;if(active==='market')active='team';if(active==='daily-pickem'||active==='daily-guess')active='daily-games';$$('.nav-tab').forEach(b=>b.classList.toggle('active',b.dataset.jump===active))}
function renderWorldSelectors(){const options=worldOrder.map(w=>`<option value="${w}">${worlds[w].label}</option>`).join('');['worldSelector','filterDivision','rankingWorld'].forEach(id=>{const el=$('#'+id);if(!el)return;el.innerHTML=options;el.value=id==='rankingWorld'?state.rankingWorld:state.activeWorld});if($('#profileBudget'))$('#profileBudget').textContent=money(totalBudget());if($('#profilePlayers'))$('#profilePlayers').textContent=selectedPlayerIds().length;if($('#profileRank')&&!$('#profileRank').textContent.trim())$('#profileRank').textContent='#4,281';const title=document.querySelector('.profile-panel h3');const sub=document.querySelector('.profile-panel p');if(title)title.textContent=state.profile.team||'Campus Eleven F.C.';if(sub)sub.textContent=`@${state.profile.handle||'manager'} · 2026 season`;if($('.avatar'))$('.avatar').textContent=state.profile.initials||'LC'}
function show(id){
 // Navigation must never wait on NCAA.com, SQLite reads, or the large player roster.
 // Paint the requested page immediately; local cache hydration happens afterward.
 $$('.page').forEach(p=>p.classList.toggle('active',p.id===id));
 markActiveNav();
 window.scrollTo({top:0,behavior:'auto'});
 if(id==='dashboard'){renderDashboard();return}
 if(id==='team'){
   // The lineup shell is completely local. Do not download the 5k+ player roster
   // just because the user opened this page; that work made every subsequent
   // click feel frozen while JSON was parsed/rendered on the main thread.
   renderTeam();
   return
 }
 if(id==='market'){
   renderMarket();
   return
 }
 if(id==='rankings'){
   renderRankings();
   if(!state.filtersLoaded) setTimeout(()=>ensureFiltersLoaded().then(()=>{if($('.page.active')?.id==='rankings')renderRankings()}),0);
   return
 }
 if(id==='competitions'){renderCompetitions();return}
 if(id==='daily-games'){renderDailyGames();return}
 if(id==='daily-pickem'){renderDailyPickem();setTimeout(()=>loadDailyPickemForDate(state.dailyPickemDate),0);return}
 if(id==='daily-guess'){renderDailyGuess();setTimeout(()=>loadDailyGuess(),0);return}
 if(id==='games'){
   renderGames();
   // Only read local SQLite caches after the page is already visible. Never
   // auto-refresh NCAA or prefetch seven dates from a navigation click.
   setTimeout(()=>syncSelectedGameDate(state.gameDate||isoToday()),0);
   setTimeout(()=>Promise.all([ensureFiltersLoaded(),ensureExtendedGamesLoaded(),ensureCoverageLoaded()]).then(()=>{if($('.page.active')?.id==='games')renderGames()}),0);
 }
}
function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),1800)}
function openModal(html){$('#modalBody').innerHTML=html;$('#modal').classList.add('show')}
function closeModal(){$('#modal').classList.remove('show');$('#modal .modal-card').classList.remove('prediction-modal')}

async function ensureFiltersLoaded(){
 if(state.filtersLoaded)return;
 const world=state.activeWorld, token=state.loadToken;
 const apiFilters=await jfetch(query('/api/filters',{division:world}),{conferences:[],schools:[],teams:[]});
 if(state.activeWorld!==world||state.loadToken!==token)return;
 state.filters={conferences:apiFilters?.conferences||[],schools:apiFilters?.schools||[]};
 state.teamRows=apiFilters?.teams||[];state.filtersLoaded=true;buildFilters();
}

async function ensureExtendedGamesLoaded(){
 if(state.extendedGamesLoaded)return;
 const world=state.activeWorld, token=state.loadToken;
 const games=await jfetch(query('/api/games',{division:world,since:isoOffset(-7),until:isoOffset(60)}),[]);
 if(state.activeWorld!==world||state.loadToken!==token)return;
 if(Array.isArray(games))mergeGames(games);state.extendedGamesLoaded=true;
}

async function ensureCoverageLoaded(){
 if(state.coverageLoaded)return;
 const world=state.activeWorld, token=state.loadToken;
 const [coverage,stats]=await Promise.all([
  jfetch(query('/api/game-coverage',{division:world}),{games:0,schools_with_games:0,by_school:[]}),
  jfetch(query('/api/player-stats-coverage',{division:world}),{players:0,players_with_verified_stats:0,schools:0,schools_with_verified_stats:0,running:false})
 ]);
 if(state.activeWorld!==world||state.loadToken!==token)return;
 state.gameCoverage=coverage||null;state.statsCoverage=stats||null;state.coverageLoaded=true;
}

async function ensureRosterLoaded(){
 if(state.rosterLoaded)return true;
 if(state.rosterPromise)return state.rosterPromise;
 const world=state.activeWorld, token=state.loadToken;
 state.rosterPromise=(async()=>{
  const apiPlayers=await jfetch(query('/api/players',{division:world}),[],15000);
  if(state.activeWorld!==world||state.loadToken!==token)return false;
  const players=(Array.isArray(apiPlayers)?apiPlayers:[]).map(normalizeApiPlayer);
  if(players.length){state.players=players;state.rosterLoaded=true;state.playerBuckets={GK:true,DF:true,MF:true,FW:true,all:true}}
  return state.rosterLoaded;
 })();
 try{return await state.rosterPromise}finally{state.rosterPromise=null}
}
async function ensurePlayersForPosition(position='all'){
 const pos=position||'all';
 if(pos==='all')return ensureRosterLoaded();
 if(state.rosterLoaded||state.playerBuckets?.[pos])return true;
 const world=state.activeWorld, token=state.loadToken;
 const key=`${world}:${pos}`;
 state.marketPromises=state.marketPromises||{};
 if(state.marketPromises[key])return state.marketPromises[key];
 state.marketLoading=true;if($('.page.active')?.id==='market')renderMarket();
 state.marketPromises[key]=(async()=>{
  const apiPlayers=await jfetch(query('/api/players',{division:world,position:pos}),[],10000);
  if(state.activeWorld!==world||state.loadToken!==token)return false;
  const incoming=(Array.isArray(apiPlayers)?apiPlayers:[]).map(normalizeApiPlayer);
  if(incoming.length){
   const byId=new Map((state.players||[]).map(p=>[p.id,p]));
   incoming.forEach(p=>byId.set(p.id,p));state.players=[...byId.values()];
  }
  state.playerBuckets=state.playerBuckets||{};state.playerBuckets[pos]=true;
  return incoming.length>0;
 })();
 try{return await state.marketPromises[key]}finally{delete state.marketPromises[key];state.marketLoading=false}
}
async function ensureCoachesLoaded(){
 if(state.coachesLoaded)return true;
 if(state.coachPromise)return state.coachPromise;
 const world=state.activeWorld, token=state.loadToken;
 state.marketLoading=true;if($('.page.active')?.id==='market')renderMarket();
 state.coachPromise=(async()=>{
  const apiCoaches=await jfetch(query('/api/coaches',{division:world}),[],8000);
  if(state.activeWorld!==world||state.loadToken!==token)return false;
  state.coaches=(Array.isArray(apiCoaches)?apiCoaches:[]).map(c=>({...c,id:`API-C${c.id}`,rating:clamp(Math.round(75+((Number(c.price||5)-4)/6)*23),75,98),verified:Boolean(c.source_url),hasStats:true}));
  state.coachesLoaded=state.coaches.length>0;return state.coachesLoaded;
 })();
 try{return await state.coachPromise}finally{state.coachPromise=null;state.marketLoading=false}
}
async function ensureMarketData(entity='players',position='all'){
 if(entity==='players')await ensurePlayersForPosition(position);
 else await ensureCoachesLoaded();
 if($('.page.active')?.id==='market'){refreshMarketDependentFilters();renderMarket()}
 if($('.page.active')?.id==='team')renderTeam();
}

async function loadWorld(world){
 state.activeWorld=world; ws(world); save(); renderWorldSelectors();state.marketVisibleCount=60;state.loadToken++;
 const cachedDash=state.dashboardCache?.[world]||{};
 state.players=[];state.coaches=[];state.games=Array.isArray(cachedDash.games)?cachedDash.games:[];state.news=Array.isArray(cachedDash.news)?cachedDash.news:[];state.prospects=Array.isArray(cachedDash.prospects)?cachedDash.prospects:[];state.filters={conferences:[],schools:[]};state.teamRows=[];
 state.gameCoverage=null;state.statsCoverage=null;state.rosterLoaded=false;state.rosterPromise=null;state.playerBuckets={};state.coachesLoaded=false;state.coachPromise=null;state.marketLoading=false;state.marketPromises={};state.filtersLoaded=false;state.extendedGamesLoaded=false;state.coverageLoaded=false;
 buildFilters();renderAll();

 const token=state.loadToken;
 const today=isoToday();
 // First paint is CACHE ONLY.  Do not make the evaluator wait on NCAA or
 // school websites just to open the dashboard.  Fresh network checks run after
 // the cached dashboard is already visible.
 const [apiNews,scoreboard,todayGames,nearGames]=await Promise.all([
  jfetch(query('/api/news',{division:world,limit:8}),state.news,2200),
  jfetch(query('/api/scoreboard-preview',{division:world}),state.games.filter(g=>g.game_date===today),2200),
  jfetch(query('/api/games-date',{division:world,date:today}),{items:state.games.filter(g=>g.game_date===today)},2200),
  jfetch(query('/api/games',{division:world,since:today,until:isoOffset(10)}),state.games.filter(g=>g.game_date>=today&&g.game_date<=isoOffset(10)),2200)
 ]);
 if(state.activeWorld!==world||state.loadToken!==token)return;
 state.news=Array.isArray(apiNews)?apiNews:[];
 const todayRows=Array.isArray(todayGames)?todayGames:(todayGames?.items||[]);
 const nearbyRows=(Array.isArray(nearGames)?nearGames:[]).filter(g=>g?.game_date!==today);
 state.games=[];
 mergeGames(verifiedGameSnapshots[world]?.[today]||[]);
 mergeGames(nearbyRows);
 if(todayRows.length)replaceGameDate(today,todayRows);
 mergeGames(Array.isArray(scoreboard)?scoreboard:[]);
 dedupeStateGames();
 state.gameConference='all';state.gameSchool='all';state.predConference='all';state.predSchool='all';state.predPage=1;
 cacheDashboardWorld(world);
 renderAll();
 loadProspects().then(()=>cacheDashboardWorld(world));
 // Keep startup interaction-first. The prepared SQLite cache already contains
 // schedule/results/news/leaderboards. Large roster reads and all public-source
 // refreshes happen only when the user opens the relevant page or presses a
 // Refresh/Sync control. This prevents background work from making every button lag.
}
function seedDefaultLineup(){const s=ws();s.seeded=true;save()}
function marketEntityPool(){
 const entity=$('#filterEntity')?.value||'players';
 if(entity==='players')return state.players;
 return state.coaches.filter(c=>entity==='Head Coach'?c.role==='Head Coach':c.role!=='Head Coach');
}
function optionHtml(value,label=value){return `<option value="${value}">${label}</option>`}
function refreshMarketDependentFilters(changed=''){
 const entity=$('#filterEntity')?.value||'players', pos=$('#filterPos'), conf=$('#filterConf'), school=$('#filterSchool'), cls=$('#filterClass');
 if(!conf||!school)return;
 let pool=marketEntityPool();
 if(entity==='players'&&pos&&pos.value!=='all')pool=pool.filter(x=>x.position===pos.value);
 if(entity==='players'&&cls&&cls.value!=='all')pool=pool.filter(x=>classNorm(x.class_year)===cls.value);
 pos.disabled=entity!=='players'; cls.disabled=entity!=='players';
 if(entity!=='players'){pos.value='all';cls.value='all'}
 // Choosing a school snaps the conference filter to that school's conference when unambiguous.
 if(changed==='school'&&school.value!=='all'){
   const confs=[...new Set(pool.filter(x=>x.school===school.value).map(x=>x.conference).filter(Boolean))];
   if(confs.length===1)conf.value=confs[0];
 }
 const previousConf=conf.value||'all';
 const confs=[...new Set(pool.map(x=>x.conference).filter(Boolean))].sort();
 conf.innerHTML=optionHtml('all',tr('allConferences'))+confs.map(x=>optionHtml(x)).join('');
 conf.value=confs.includes(previousConf)?previousConf:'all';
 let schoolPool=pool;
 if(conf.value!=='all')schoolPool=schoolPool.filter(x=>x.conference===conf.value);
 const previousSchool=school.value||'all';
 const schools=[...new Set(schoolPool.map(x=>x.school).filter(Boolean))].sort();
 school.innerHTML=optionHtml('all',tr('allSchools'))+schools.map(x=>optionHtml(x)).join('');
 school.value=schools.includes(previousSchool)?previousSchool:'all';
 state.filters.conferences=confs; state.filters.schools=schools;
}
function buildFilters(){refreshMarketDependentFilters();dedupeStateGames();renderRankingConferenceOptions()}
function renderAll(){
 const active=$('.page.active')?.id||'dashboard';
 if(active==='dashboard')renderDashboard();
 else if(active==='team')renderTeam();
 else if(active==='market')renderMarket();
 else if(active==='rankings')renderRankings();
 else if(active==='competitions')renderCompetitions();
 else if(active==='games')renderGames();
 else if(active==='daily-games')renderDailyGames();
 else if(active==='daily-pickem')renderDailyPickem();
 else if(active==='daily-guess')renderDailyGuess();
}


function isoShiftDate(base,days){const [y,m,d]=String(base||isoToday()).split('-').map(Number);const x=new Date(y,m-1,d,12);x.setDate(x.getDate()+Number(days||0));return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,'0')}-${String(x.getDate()).padStart(2,'0')}`}
function dailyNiceDate(value){const [y,m,d]=String(value||isoToday()).split('-').map(Number);return new Date(y,m-1,d,12).toLocaleDateString(state.lang==='pt'?'pt-BR':state.lang==='es'?'es-ES':'en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'})}
function dailyGameState(world=state.activeWorld){
 let root=state.dailyGames[world];
 if(!root||typeof root!=='object')root={};
 if(!root.pickemByDate)root.pickemByDate={};
 if(!root.guessByDate)root.guessByDate={};
 // One-time migration: reset only Guess the Player progress when switching
 // from the old one-player format to the five-player daily format.
 if(root.guessModeVersion!=='five-round-v1'){
  root.guessByDate={};
  root.guessModeVersion='five-round-v1';
 }
 if(!Number.isFinite(Number(root.streak)))root.streak=0;
 if(!('lastCompletedDate' in root))root.lastCompletedDate=null;
 state.dailyGames[world]=root;return root;
}
function dailyPickRecord(date=isoToday(),world=state.activeWorld){
 const root=dailyGameState(world);
 if(!root.pickemByDate[date])root.pickemByDate[date]={picks:{},submittedPicks:{},submitted:false,submittedAt:null,completed:false,waived:false,score:0};
 const r=root.pickemByDate[date];
 if(!r.picks||typeof r.picks!=='object')r.picks={};
 if(!r.submittedPicks||typeof r.submittedPicks!=='object')r.submittedPicks={};
 if(!('submitted' in r))r.submitted=false;
 if(!('submittedAt' in r))r.submittedAt=null;
 return r
}
function dailyGuessKey(date=isoToday(),round=state.dailyGuessRound||1){return `${date}#${Math.max(1,Math.min(DAILY_GUESS_ROUNDS,Number(round)||1))}`}
function dailyGuessRecord(date=isoToday(),world=state.activeWorld,round=state.dailyGuessRound||1){const root=dailyGameState(world),key=dailyGuessKey(date,round);if(!root.guessByDate[key])root.guessByDate[key]={questions:[],guesses:[],completed:false,solved:false,failed:false,score:0,answerKey:null};const r=root.guessByDate[key];if(!Array.isArray(r.questions))r.questions=[];if(!Array.isArray(r.guesses))r.guesses=[];return r}
function dailyGuessRecords(date=isoToday(),world=state.activeWorld){return Array.from({length:DAILY_GUESS_ROUNDS},(_,i)=>dailyGuessRecord(date,world,i+1))}
function dailyGuessCompletedCount(date=isoToday(),world=state.activeWorld){return dailyGuessRecords(date,world).filter(r=>r.completed).length}
function dailyGuessAllComplete(date=isoToday(),world=state.activeWorld){return dailyGuessCompletedCount(date,world)>=DAILY_GUESS_ROUNDS}
function dailyGuessScoreTotal(date=isoToday(),world=state.activeWorld){return dailyGuessRecords(date,world).reduce((sum,r)=>sum+Number(r.score||0),0)}
function dailyUpdateStreak(world=state.activeWorld){const root=dailyGameState(world),today=isoToday(),pick=dailyPickRecord(today,world);if(!(pick.completed&&dailyGuessAllComplete(today,world)))return;if(root.lastCompletedDate===today)return;root.streak=root.lastCompletedDate===isoShiftDate(today,-1)?Number(root.streak||0)+1:1;root.lastCompletedDate=today;save()}
function dailyTodayPoints(world=state.activeWorld){const p=dailyPickRecord(isoToday(),world);return Number(p.score||0)+dailyGuessScoreTotal(isoToday(),world)}
function renderDailyGames(){
 renderWorldSelectors();const root=dailyGameState(),pick=dailyPickRecord(),guessDone=dailyGuessCompletedCount();dailyUpdateStreak();
 const guessComplete=guessDone>=DAILY_GUESS_ROUNDS,completed=Number(Boolean(pick.completed))+Number(guessComplete),label=worlds[state.activeWorld]?.label||state.activeWorld;
 const worldLabel=$('#dailyGamesWorldLabel');if(worldLabel)worldLabel.textContent=`${label} WORLD`;
 if($('#dailyProgressValue'))$('#dailyProgressValue').textContent=`${completed}/2`;if($('#dailyProgressBar'))$('#dailyProgressBar').style.width=`${completed*50}%`;if($('#dailyStreakValue'))$('#dailyStreakValue').textContent=String(root.streak||0);if($('#dailyPointsValue'))$('#dailyPointsValue').textContent=String(dailyTodayPoints());
 const switcher=$('#dailyWorldSwitcher');if(switcher){switcher.innerHTML=worldOrder.map(w=>`<button class="${w===state.activeWorld?'active':''}" data-daily-world="${w}"><span>${worlds[w].label}</span><small>${w===state.activeWorld?'ACTIVE WORLD':'OPEN WORLD'}</small></button>`).join('');$$('[data-daily-world]').forEach(b=>b.onclick=()=>{const next=b.dataset.dailyWorld;if(!next||next===state.activeWorld)return;state.dailyGuessRound=1;state.dailyGuessRuntime=null;state.dailyGuessSelected=null;void loadWorld(next).then(()=>{if($('.page.active')?.id==='daily-games')renderDailyGames()})})}
 const pickBtn=$('[data-daily-preview="pickem"]'),guessBtn=$('[data-daily-preview="guess"]');if(pickBtn){pickBtn.textContent=pick.completed?(pick.waived?'NO GAMES TODAY →':'PICK\'EM COMPLETE ✓'):(Object.keys(pick.picks||{}).length?'CONTINUE PICK\'EM →':'PLAY PICK\'EM →');pickBtn.onclick=()=>{state.dailyPickemMode='today';state.dailyPickemDate=isoToday();show('daily-pickem')}}if(guessBtn){const next=Math.min(DAILY_GUESS_ROUNDS,guessDone+1);guessBtn.textContent=guessComplete?'5/5 COMPLETE ✓':`${guessDone?`CONTINUE ${guessDone}/5`:`PLAY PLAYER 1/5`} →`;guessBtn.onclick=()=>{state.dailyGuessRound=next;state.dailyGuessRuntime=null;state.dailyGuessSelected=null;show('daily-guess')}}
 save();
}
function etNowParts(){const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date());const o={};parts.forEach(x=>o[x.type]=x.value);return{date:`${o.year}-${o.month}-${o.day}`,minutes:Number(o.hour)*60+Number(o.minute)}}
function gameStartMinutes(g){const m=String(g?.start_time||'').match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);if(!m)return null;let h=Number(m[1])%12;if(m[3].toUpperCase()==='PM')h+=12;return h*60+Number(m[2])}
function dailyGameMinuteStamp(date,minutes){
 const p=String(date||'').split('-').map(Number);if(p.length!==3||p.some(x=>!Number.isFinite(x)))return null;
 return Math.floor(Date.UTC(p[0],p[1]-1,p[2])/60000)+Number(minutes||0)
}
function dailyGameLocked(g){
 if(isLive(g)||isFinal(g))return true;
 const start=gameStartMinutes(g);if(start===null)return false;
 const gameStamp=dailyGameMinuteStamp(g?.game_date,start);if(gameStamp===null)return false;
 const now=etNowParts(),nowStamp=dailyGameMinuteStamp(now.date,now.minutes);if(nowStamp===null)return false;
 return nowStamp>=gameStamp-60
}
function dailyGameKey(g){return String(g.id||`${g.game_date}|${g.away_team}|${g.home_team}|${g.start_time||''}`)}
function dailyActualOutcome(g){if(!isFinal(g)||g.home_score===null||g.home_score===undefined||g.away_score===null||g.away_score===undefined)return null;const h=Number(g.home_score),a=Number(g.away_score);return h>a?'home':a>h?'away':'draw'}
function normalizeDailyPick(p){
 if(!p)return null;
 if(typeof p==='string')return{outcome:p,home_score:null,away_score:null};
 return{outcome:String(p.outcome||p.pick||''),home_score:p.home_score===''||p.home_score===null||p.home_score===undefined?null:Number(p.home_score),away_score:p.away_score===''||p.away_score===null||p.away_score===undefined?null:Number(p.away_score)}
}
function dailyPickOutcomeFromScore(h,a){h=Number(h);a=Number(a);if(!Number.isFinite(h)||!Number.isFinite(a))return'';return h>a?'home':a>h?'away':'draw'}
function dailyPickHasExact(p){p=normalizeDailyPick(p);return Boolean(p&&Number.isInteger(p.home_score)&&p.home_score>=0&&Number.isInteger(p.away_score)&&p.away_score>=0)}
function dailyPickMade(p){p=normalizeDailyPick(p);return Boolean(p?.outcome)}
function gradeDailyPickem(games,rec){
 let score=0,correct=0,graded=0,exact=0;const picks=rec.submittedPicks||{};
 games.forEach(g=>{
  const actual=dailyActualOutcome(g),p=normalizeDailyPick(picks[dailyGameKey(g)]);if(!actual||!p?.outcome)return;
  graded++;
  const exactHit=dailyPickHasExact(p)&&Number(g.home_score)===p.home_score&&Number(g.away_score)===p.away_score;
  if(exactHit){score+=20;correct++;exact++;return}
  if(p.outcome===actual){score+=10;correct++}
 });
 rec.score=score;return{score,correct,graded,exact,made:games.filter(g=>dailyPickMade(picks[dailyGameKey(g)])).length,total:games.length}
}
function pickemCacheKey(world,date){return `${world}|${date}`}
async function fetchDailyPickemDate(date,world=state.activeWorld){const key=pickemCacheKey(world,date);if(Array.isArray(state.dailyPickemCache[key]))return state.dailyPickemCache[key];const payload=await jfetch(query('/api/games-date',{division:world,date}),{items:[]},2600);const items=Array.isArray(payload)?payload:(payload?.items||[]);state.dailyPickemCache[key]=items;return items}
async function loadDailyPickemForDate(date=state.dailyPickemDate){const world=state.activeWorld,key=pickemCacheKey(world,date);if(Array.isArray(state.dailyPickemCache[key])){renderDailyPickem();return}state.dailyPickemLoading=true;renderDailyPickem();await fetchDailyPickemDate(date,world);if(world!==state.activeWorld||date!==state.dailyPickemDate)return;state.dailyPickemLoading=false;renderDailyPickem()}
async function setDailyPickemMode(mode){state.dailyPickemMode=mode;if(mode==='today'){state.dailyPickemDate=isoToday();renderDailyPickem();return loadDailyPickemForDate(state.dailyPickemDate)}state.dailyPickemLoading=true;renderDailyPickem();const offsets=mode==='upcoming'?[1,2,3,4,5,6,7]:[-1,-2,-3,-4,-5,-6,-7];const world=state.activeWorld;const results=await Promise.all(offsets.map(async off=>{const date=isoShiftDate(isoToday(),off);return{date,items:await fetchDailyPickemDate(date,world)}}));if(world!==state.activeWorld)return;const found=results.find(x=>mode==='results'?x.items.some(isFinal):x.items.length)||results[0];state.dailyPickemDate=found.date;state.dailyPickemLoading=false;renderDailyPickem()}
function renderDailyPickem(){
 renderWorldSelectors();
 const world=state.activeWorld,label=worlds[world]?.label||world,date=state.dailyPickemDate||isoToday(),key=pickemCacheKey(world,date),games=state.dailyPickemCache[key];
 if($('#dailyPickemWorldBadge'))$('#dailyPickemWorldBadge').textContent=label;
 if($('#dailyPickemWorldCopy'))$('#dailyPickemWorldCopy').textContent=`Pick every ${label} match your way — quick winner or exact score. Picks lock 1 hour before kickoff.`;
 if($('#dailyPickemDate'))$('#dailyPickemDate').value=date;
 if($('#dailyPickemDateLabel'))$('#dailyPickemDateLabel').textContent=dailyNiceDate(date);
 $$('[data-pickem-mode]').forEach(b=>b.classList.toggle('active',b.dataset.pickemMode===state.dailyPickemMode));
 const wrap=$('#dailyPickemGames');if(!wrap)return;
 if(!Array.isArray(games)){wrap.innerHTML='<div class="daily-loading">Loading matches…</div>';if(!state.dailyPickemLoading)setTimeout(()=>loadDailyPickemForDate(date),0);return}
 const rec=dailyPickRecord(date,world);
 if(date===isoToday()&&games.length===0){rec.waived=true;rec.completed=true}
 else if(date===isoToday()&&games.length){rec.waived=false;rec.completed=games.every(g=>dailyPickMade(rec.submittedPicks[dailyGameKey(g)]))}
 const grade=gradeDailyPickem(games,rec);
 if($('#dailyPickemScore'))$('#dailyPickemScore').textContent=grade.score;
 if($('#dailyPickemMade'))$('#dailyPickemMade').textContent=`${grade.made}/${grade.total}`;
 if($('#dailyPickemCorrect'))$('#dailyPickemCorrect').textContent=String(grade.correct);
 if($('#dailyPickemStatus'))$('#dailyPickemStatus').textContent=games.length?(games.every(dailyGameLocked)?'LOCKED':rec.submitted?'SUBMITTED':'OPEN'):'NO GAMES';
 if($('#dailyPickemStatusSub'))$('#dailyPickemStatusSub').textContent=games.length?(rec.submitted?'Editable until 1 hour before each kickoff':'Submit picks to make them official · locks 1 hour before kickoff'):'This day does not count against your streak';
 const cleanPickMap=obj=>Object.fromEntries(Object.entries(obj||{}).filter(([,v])=>dailyPickMade(v)).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,normalizeDailyPick(v)]));
 const samePick=(a,b)=>JSON.stringify(normalizeDailyPick(a))===JSON.stringify(normalizeDailyPick(b));
 const draftMap=cleanPickMap(rec.picks),submittedMap=cleanPickMap(rec.submittedPicks);
 const hasChanges=JSON.stringify(draftMap)!==JSON.stringify(submittedMap);
 if(!games.length){
  wrap.innerHTML=`<div class="daily-empty"><div class="daily-empty-icon">⚽</div><h3>No ${label} matches stored for this date.</h3><p>Use the date arrows or Upcoming to find the next matchday.</p></div>`;
 }else{
  const cards=games.map((g,index)=>{
   const k=dailyGameKey(g),locked=dailyGameLocked(g),actual=dailyActualOutcome(g),final=Boolean(actual);
   const draftPick=normalizeDailyPick(rec.picks[k]),submittedPick=normalizeDailyPick(rec.submittedPicks[k]);
   const pick=(locked||final)?submittedPick:draftPick;
   const home=String(g.home_team||'Home'),away=String(g.away_team||'Away');
   const homeMeta=teamMeta(home),awayMeta=teamMeta(away);
   const homeAbbr=homeMeta?.abbreviation||home.split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase();
   const awayAbbr=awayMeta?.abbreviation||away.split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase();
   const pickClass=o=>pick?.outcome===o?(final?(actual===o?'selected correct':'selected wrong'):'selected'):'';
   const disabled=locked?'disabled':'';
   const exactHit=final&&submittedPick&&dailyPickHasExact(submittedPick)&&Number(g.home_score)===submittedPick.home_score&&Number(g.away_score)===submittedPick.away_score;
   const outcomeHit=final&&submittedPick?.outcome===actual;
   const earned=exactHit?20:outcomeHit?10:0;
   const conference=[gameConference(g,'home'),gameConference(g,'away')].filter(Boolean).filter((x,i,a)=>a.indexOf(x)===i).join(' · ');
   const resultBlock=final?`<div class="college-pick-result"><small>FINAL</small><strong>${g.home_score} <span>–</span> ${g.away_score}</strong></div>`:`<div class="college-pick-time"><small>${g.game_date===isoToday()?'TODAY':'MATCHDAY'}</small><strong>${g.start_time||'TBD'}</strong>${locked?'<span>LOCKED · 1H BEFORE</span>':''}</div>`;
   const official=submittedPick?.outcome?`<small class="pick-official">${rec.submitted?'SUBMITTED':'SAVED'}</small>`:'';
   const changed=!locked&&!final&&!samePick(draftPick,submittedPick);
   const summaryPick=(locked||final)?submittedPick:draftPick;
   const summary=summaryPick?.outcome?`<div class="college-your-pick"><span>YOUR PICK ${changed?'<i>UNSUBMITTED CHANGE</i>':official}</span><b>${dailyPickHasExact(summaryPick)?`${homeAbbr} ${summaryPick.home_score}–${summaryPick.away_score} ${awayAbbr}`:(summaryPick.outcome==='home'?`${home} to win`:summaryPick.outcome==='away'?`${away} to win`:'Draw')}</b>${final?`<em class="${earned===20?'exact':earned===10?'right':'miss'}">${earned===20?'EXACT SCORE':earned===10?'CORRECT OUTCOME':'MISS'} · +${earned}</em>`:''}${!locked&&!final?`<button class="college-clear-pick" data-clear-pick="${k}">CLEAR PICK</button>`:''}</div>`:`<div class="college-your-pick empty"><span>YOUR PICK</span><b>Not selected yet</b></div>`;
   return `<article class="college-pick-row ${final?'final':''}" data-college-pick-index="${index}">
    <div class="college-pick-meta"><span class="college-match-no">${String(index+1).padStart(2,'0')}</span><div><b>${g.conference_game?'CONFERENCE MATCH':'COLLEGE MATCH'}</b><small>${conference||label}</small></div>${resultBlock}</div>
    <div class="college-matchup">
      <div class="college-team home"><div><strong>${home}</strong><small>HOME</small></div><span class="college-team-mark">${homeAbbr.slice(0,3)}</span></div>
      <div class="college-vs">VS</div>
      <div class="college-team away"><span class="college-team-mark">${awayAbbr.slice(0,3)}</span><div><strong>${away}</strong><small>AWAY</small></div></div>
    </div>
    <div class="college-pick-actions">
      <div class="college-pick-section"><div class="college-pick-label"><span>QUICK PICK</span><small>Winner only · 10 pts · click again to clear</small></div><div class="college-winner-buttons">
       <button ${disabled} class="college-winner ${pickClass('home')}" data-pickem-game="${k}" data-pickem-pick="home"><span>1</span><b>${homeAbbr}</b></button>
       <button ${disabled} class="college-winner draw ${pickClass('draw')}" data-pickem-game="${k}" data-pickem-pick="draw"><span>X</span><b>DRAW</b></button>
       <button ${disabled} class="college-winner ${pickClass('away')}" data-pickem-game="${k}" data-pickem-pick="away"><span>2</span><b>${awayAbbr}</b></button>
      </div></div>
      <div class="college-exact-section"><div class="college-pick-label"><span>EXACT SCORE</span><small>Hit the score · 20 pts</small></div><div class="college-score-inputs">
       <label><small>${homeAbbr}</small><input ${disabled} inputmode="numeric" pattern="[0-9]*" min="0" max="30" type="number" data-exact-home="${k}" value="${dailyPickHasExact(pick)?pick.home_score:''}" placeholder="–"></label>
       <span>:</span>
       <label><small>${awayAbbr}</small><input ${disabled} inputmode="numeric" pattern="[0-9]*" min="0" max="30" type="number" data-exact-away="${k}" value="${dailyPickHasExact(pick)?pick.away_score:''}" placeholder="–"></label>
      </div></div>
      ${summary}
    </div>
   </article>`
  }).join('');
  const openGames=games.filter(g=>!dailyGameLocked(g));
  const draftCount=openGames.filter(g=>dailyPickMade(rec.picks[dailyGameKey(g)])).length;
  const submitLabel=rec.submitted?(hasChanges?'UPDATE PICKS':'PICKS SUBMITTED ✓'):'SUBMIT PICKS';
  const submitDisabled=!openGames.length||(!hasChanges&&rec.submitted)||(!draftCount&&!rec.submitted);
  const submitCopy=rec.submitted?(hasChanges?'You have changes that are not official yet. Submit again before each match locks.':'Your picks are official. You can still edit and resubmit until 1 hour before kickoff.'):'Selections are drafts until you submit them. You may leave any match blank.';
  wrap.innerHTML=cards+`<section class="pickem-submit-panel ${rec.submitted&&!hasChanges?'submitted':''}"><div><span class="pickem-submit-kicker">PICK SHEET</span><h3>${rec.submitted?'Your picks are on the board.':'Ready to lock in your calls?'}</h3><p>${submitCopy}</p><div class="pickem-submit-meta"><span>${draftCount} current pick${draftCount===1?'':'s'}</span><span>🔒 Locks 1 hour before kickoff</span><span>20 exact · 10 outcome · 0 miss</span></div></div><button id="submitDailyPickem" class="pickem-submit-btn" ${submitDisabled?'disabled':''}>${submitLabel}</button></section>`;
 }
 $$('[data-pickem-game]').forEach(b=>b.onclick=()=>{
  const k=b.dataset.pickemGame,g=games.find(x=>dailyGameKey(x)===k);if(!g||dailyGameLocked(g)){toast('Picks lock 1 hour before kickoff.');return}
  const current=normalizeDailyPick(rec.picks[k]);
  if(current?.outcome===b.dataset.pickemPick&&!dailyPickHasExact(current))delete rec.picks[k];
  else rec.picks[k]={outcome:b.dataset.pickemPick,home_score:null,away_score:null};
  save();renderDailyPickem()
 });
 $$('[data-clear-pick]').forEach(b=>b.onclick=()=>{const k=b.dataset.clearPick,g=games.find(x=>dailyGameKey(x)===k);if(!g||dailyGameLocked(g))return;delete rec.picks[k];save();renderDailyPickem()});
 const saveExact=(k)=>{
  const g=games.find(x=>dailyGameKey(x)===k);if(!g||dailyGameLocked(g)){toast('Picks lock 1 hour before kickoff.');return}
  const h=$(`[data-exact-home="${CSS.escape(k)}"]`),a=$(`[data-exact-away="${CSS.escape(k)}"]`);if(!h||!a)return;
  const hv=h.value,av=a.value;
  if(hv===''||av===''){if(hv===''&&av===''){delete rec.picks[k];save();renderDailyPickem()}return}
  const hs=Math.max(0,Math.min(30,Number(hv))),as=Math.max(0,Math.min(30,Number(av)));if(!Number.isFinite(hs)||!Number.isFinite(as))return;
  rec.picks[k]={outcome:dailyPickOutcomeFromScore(hs,as),home_score:Math.trunc(hs),away_score:Math.trunc(as)};
  save();renderDailyPickem()
 };
 $$('[data-exact-home],[data-exact-away]').forEach(input=>input.onchange=()=>saveExact(input.dataset.exactHome||input.dataset.exactAway));
 const submit=$('#submitDailyPickem');if(submit)submit.onclick=()=>{
  const next={...rec.submittedPicks};
  games.forEach(g=>{const k=dailyGameKey(g);if(dailyGameLocked(g))return;const p=normalizeDailyPick(rec.picks[k]);if(p?.outcome)next[k]=p;else delete next[k]});
  rec.submittedPicks=next;rec.submitted=true;rec.submittedAt=new Date().toISOString();
  rec.completed=date===isoToday()?games.every(g=>dailyPickMade(rec.submittedPicks[dailyGameKey(g)])):rec.completed;
  gradeDailyPickem(games,rec);dailyUpdateStreak(world);save();toast('Picks submitted. You can edit and resubmit until 1 hour before kickoff.');renderDailyPickem()
 };
 if($('#dailyPickemPrev'))$('#dailyPickemPrev').onclick=()=>{state.dailyPickemMode='custom';state.dailyPickemDate=isoShiftDate(date,-1);renderDailyPickem();loadDailyPickemForDate(state.dailyPickemDate)};
 if($('#dailyPickemNext'))$('#dailyPickemNext').onclick=()=>{state.dailyPickemMode='custom';state.dailyPickemDate=isoShiftDate(date,1);renderDailyPickem();loadDailyPickemForDate(state.dailyPickemDate)};
 if($('#dailyPickemDate'))$('#dailyPickemDate').onchange=e=>{state.dailyPickemMode='custom';state.dailyPickemDate=e.target.value||isoToday();renderDailyPickem();loadDailyPickemForDate(state.dailyPickemDate)};
 $$('[data-pickem-mode]').forEach(b=>b.onclick=()=>setDailyPickemMode(b.dataset.pickemMode));dailyUpdateStreak(world);save();
}

function dailyHash(text){let h=2166136261;for(const ch of String(text)){h^=ch.charCodeAt(0);h=Math.imul(h,16777619)}return h>>>0}
function dailyPlayerKey(p){return String(p?.id??`${String(p?.name||'').trim().toLowerCase()}|${String(p?.division||state.activeWorld)}`)}
function dailyQuestionAvailable(type,rt){const a=rt?.answer||{},pool=rt?.pool||{};if(type==='position')return (a.positions||[a.position]).filter(Boolean).length>0;if(type==='conference')return Array.isArray(pool.conferences)&&pool.conferences.length>0&&(a.conferences||[a.conference]).filter(Boolean).length>0;if(type==='school')return Array.isArray(pool.schools)&&pool.schools.length>0;if(type==='class')return Array.isArray(pool.classes)&&pool.classes.length>0&&Boolean(a.class_year);if(type==='season'||type==='era')return Array.isArray(pool.seasons)&&pool.seasons.length>1;if(type==='multiple')return Array.isArray(a.seasons)&&a.seasons.length>0;if(type==='tournament')return Boolean(pool.has_tournament)&&a.tournament_team!==null&&a.tournament_team!==undefined;if(type==='ranked')return Boolean(pool.has_ranked)&&a.ranked_team!==null&&a.ranked_team!==undefined;return false}
async function loadDailyGuess(){const world=state.activeWorld,date=isoToday(),round=Math.max(1,Math.min(DAILY_GUESS_ROUNDS,Number(state.dailyGuessRound)||1));if(state.dailyGuessLoading)return;if(state.dailyGuessRuntime?.world===world&&state.dailyGuessRuntime?.date===date&&Number(state.dailyGuessRuntime?.round)===round){renderDailyGuess();return}state.dailyGuessLoading=true;renderDailyGuess();const payload=await jfetch(query('/api/guess-player/today',{division:world,date,round}),null,5000);if(world!==state.activeWorld||round!==state.dailyGuessRound){state.dailyGuessLoading=false;return}if(!payload?.answer){state.dailyGuessRuntime={world,date,round,error:payload?.error||'No player data is available for this world yet.'};state.dailyGuessLoading=false;renderDailyGuess();return}const rec=dailyGuessRecord(date,world,round),answer=payload.answer,key=dailyPlayerKey(answer);if(rec.answerKey&&String(rec.answerKey)!==key){rec.questions=[];rec.guesses=[];rec.completed=false;rec.solved=false;rec.failed=false;rec.score=0}rec.answerKey=key;state.dailyGuessRuntime={world,date,round,answer,pool:payload.pool||{},poolCount:Number(payload.pool_count||0),minSeason:Number(payload.min_season||2026),maxSeason:Number(payload.max_season||2026),testMode:Boolean(payload.test_mode)};state.dailyGuessLoading=false;save();renderDailyGuess()}
function dailyQuestionOptions(type,rt){const pool=rt?.pool||{};if(type==='position')return[['FW','Forward'],['MF','Midfielder'],['DF','Defender'],['GK','Goalkeeper']];if(type==='class')return (pool.classes||['Freshman','Sophomore','Junior','Senior','Graduate']).map(x=>[classNorm(x)||x,classNorm(x)||x]);if(type==='conference')return (pool.conferences||[]).map(x=>[x,x]);if(type==='school')return (pool.schools||[]).slice(0,700).map(x=>[x,x]);if(type==='season')return (pool.seasons||[]).map(x=>[String(x),String(x)]);if(type==='era'){const ys=(pool.seasons||[]).map(Number).sort((a,b)=>a-b);return ys.slice(1).map(x=>[String(x),`${x} or later`])}if(type==='multiple')return[['yes','More than one season']];if(type==='tournament')return[['yes','Reached the national tournament']];if(type==='ranked')return[['yes','Played for a ranked team']];return[]}
function dailyQuestionText(type,value){if(type==='position')return `Was the player listed as a ${value==='FW'?'Forward':value==='MF'?'Midfielder':value==='DF'?'Defender':'Goalkeeper'}?`;if(type==='class')return `Was the player listed as a ${value} in the latest season in this pool?`;if(type==='conference')return `Did the player compete in ${value}?`;if(type==='school')return `Did the player play for ${value}?`;if(type==='season')return `Did the player play college soccer in ${value}?`;if(type==='era')return `Did the player play college soccer in or after ${value}?`;if(type==='multiple')return 'Did the player appear in more than one college season?';if(type==='tournament')return 'Did the player reach the national tournament?';if(type==='ranked')return 'Did the player play for a nationally ranked team?';return 'Question'}
function dailyQuestionAnswer(answer,type,value){if(type==='position')return (answer.positions||[answer.position]).map(normalizePosition).includes(value);if(type==='class')return classNorm(answer.class_year)===value;if(type==='conference')return (answer.conferences||[answer.conference]).map(x=>String(x||'').toLowerCase()).includes(String(value).toLowerCase());if(type==='school')return (answer.schools||[answer.school]).map(x=>String(x||'').toLowerCase()).includes(String(value).toLowerCase());if(type==='season')return (answer.seasons||[]).map(Number).includes(Number(value));if(type==='era')return Number(answer.last_season||answer.season||0)>=Number(value);if(type==='multiple')return Boolean(answer.multiple_seasons);if(type==='tournament')return Boolean(answer.tournament_team);if(type==='ranked')return Boolean(answer.ranked_team);return false}
function dailyGuessPotentialScore(rec){if(rec.failed)return 0;if(rec.solved)return Number(rec.score||0);return Math.max(20,100-rec.questions.length*4-rec.guesses.length*15)}
function populateDailyQuestionValues(){const rt=state.dailyGuessRuntime,typeEl=$('#guessQuestionType'),el=$('#guessQuestionValue');if(!el||!rt?.answer||!typeEl)return;[...typeEl.options].forEach(o=>{const ok=dailyQuestionAvailable(o.value,rt);o.hidden=!ok;o.disabled=!ok});if(typeEl.selectedOptions[0]?.disabled){const first=[...typeEl.options].find(o=>!o.disabled);if(first)typeEl.value=first.value}const type=typeEl.value,opts=dailyQuestionOptions(type,rt);el.innerHTML=opts.length?opts.map(([v,l])=>`<option value="${String(v).replace(/"/g,'&quot;')}">${l}</option>`).join(''):'<option value="">No options available</option>'}
function revealDailyMystery(rt,rec){
 const a=rt.answer;if(!a)return'';
 const seasons=(a.seasons||[]).map(Number).sort((x,y)=>x-y),seasonLabel=seasons.length>1?`${seasons[0]}–${seasons[seasons.length-1]}`:(seasons[0]||a.season||'—');
 const schools=(a.schools||[a.school]).filter(Boolean),conferences=(a.conferences||[a.conference]).filter(Boolean),pos=normalizePosition(a.position)||'—';
 const posLabel=pos==='DF'?'Defender':pos==='MF'?'Midfielder':pos==='FW'?'Forward':pos==='GK'?'Goalkeeper':pos;
 const initials=name=>String(name||'').split(/\s+/).filter(Boolean).slice(0,3).map(x=>x[0]).join('').toUpperCase();
 const nameParts=String(a.name||'').trim().split(/\s+/);
 const firstName=nameParts.shift()||'';
 const lastName=nameParts.join(' ');
 const schoolCards=schools.map(s=>{
  let years='';

  if(String(a.name||'').toLowerCase()==='pedro arcoverde'){
    if(s.toLowerCase().includes('missouri state')){
      years='2023–2024';
    }else if(s.toLowerCase().includes('florida gulf coast')){
      years='2025';
    }
  }

  return `
    <div class="reveal-history-card">
      <span>${initials(s)}</span>

      <div>
        <small>SCHOOL</small>
        <b>${s}</b>

        ${years ? `<div class="reveal-school-years">${years}</div>` : ''}
      </div>
    </div>
  `;
}).join('');
 const confCards=conferences.map(c=>`<div class="reveal-conference-chip"><span>◆</span><b>${c}</b></div>`).join('');
 return `<div class="revealed-player-pro ${rec.solved?'solved':'revealed'}">
   <div class="reveal-visual-panel">
     <div class="reveal-status-pill"><span>${rec.solved?'✓':'!'}</span>${rec.solved?'SOLVED':'ANSWER REVEALED'}</div>
     <div class="reveal-stadium-lines"></div>
     <div class="reveal-generic-player" aria-hidden="true"><i></i><b>${pos}</b></div>
     <div class="reveal-visual-caption"><small>COLLEGE SOCCER PLAYER</small><strong>${posLabel}</strong></div>
   </div>
   <div class="reveal-info-panel">
     <div class="reveal-kicker">${rec.solved?'YOU GOT IT':'THE CORRECT PLAYER WAS'}</div>
     <h3 class="reveal-player-name">
      <span class="reveal-first-name">${firstName}</span>
      <span class="reveal-last-name">${lastName}</span>
    </h3>
     <div class="reveal-position-line"><span>${posLabel}</span><b>${pos}</b></div>
     <div class="reveal-stat-grid">
       <div><small>LATEST CLASS</small><strong>${classNorm(a.class_year)||'—'}</strong></div>
       <div><small>COLLEGE YEARS</small><strong>${seasonLabel}</strong></div>
       <div><small>POSITION</small><strong>${posLabel}</strong></div>
     </div>
     <div class="reveal-section"><div class="reveal-section-title">COLLEGE HISTORY</div><div class="reveal-history-grid">${schoolCards||'<span class="reveal-muted">School history unavailable</span>'}</div></div>
     <div class="reveal-section"><div class="reveal-section-title">CONFERENCES</div><div class="reveal-conferences">${confCards||'<span class="reveal-muted">Conference unavailable</span>'}</div></div>
   </div>
 </div>
 <div class="reveal-outcome-strip ${rec.solved?'solved':'revealed'}"><div><b>${rec.solved?'Great read.':'Tough one.'}</b><span>${rec.solved?`You identified Player ${state.dailyGuessRound||1} of ${DAILY_GUESS_ROUNDS}.`:`The answer is now unlocked. Player ${state.dailyGuessRound||1} of ${DAILY_GUESS_ROUNDS} is complete.`}</span></div><strong>${rec.solved?`+${Number(rec.score||0)} pts`:'0 pts'}</strong></div>`
}
function renderDailyGuess(){
 renderWorldSelectors();const world=state.activeWorld,label=worlds[world]?.label||world,round=Math.max(1,Math.min(DAILY_GUESS_ROUNDS,Number(state.dailyGuessRound)||1)),rec=dailyGuessRecord(isoToday(),world,round),root=dailyGameState(world),rt=state.dailyGuessRuntime,done=dailyGuessCompletedCount();
 if($('#dailyGuessWorldBadge'))$('#dailyGuessWorldBadge').textContent=label;if($('#dailyGuessQuestionCount'))$('#dailyGuessQuestionCount').textContent=`${rec.questions.length}/10`;if($('#dailyGuessAttempts'))$('#dailyGuessAttempts').textContent=String(Math.max(0,3-rec.guesses.length));if($('#dailyGuessScore'))$('#dailyGuessScore').textContent=String(dailyGuessPotentialScore(rec));if($('#dailyGuessStreak'))$('#dailyGuessStreak').textContent=`${root.streak||0} 🔥`;
 const roundNav=$('#dailyGuessRoundNav');if(roundNav){roundNav.innerHTML=Array.from({length:DAILY_GUESS_ROUNDS},(_,i)=>{const n=i+1,r=dailyGuessRecord(isoToday(),world,n);return `<button class="${n===round?'active':''} ${r.completed?'completed':''}" data-guess-round="${n}"><small>PLAYER</small><b>${n}</b><span>${r.completed?(r.solved?'✓':'•'):''}</span></button>`}).join('');$$('[data-guess-round]').forEach(b=>b.onclick=()=>{const n=Number(b.dataset.guessRound);if(n===state.dailyGuessRound)return;state.dailyGuessRound=n;state.dailyGuessRuntime=null;state.dailyGuessSelected=null;if($('#dailyGuessSearch'))$('#dailyGuessSearch').value='';loadDailyGuess()})}
 if(!rt||rt.world!==world||rt.date!==isoToday()||Number(rt.round)!==round){if($('#dailyGuessWorldCopy'))$('#dailyGuessWorldCopy').textContent=`Player ${round} of ${DAILY_GUESS_ROUNDS} · today's mystery player comes only from the ${label} world.`;if($('#mysteryWorldText'))$('#mysteryWorldText').textContent=`${label} · loading player pool`;if($('#guessQuestionHistory'))$('#guessQuestionHistory').innerHTML='<div class="daily-loading">Loading today\'s player…</div>';if($('#mysteryChallengeTag'))$('#mysteryChallengeTag').textContent=`PLAYER ${round} OF ${DAILY_GUESS_ROUNDS}`;if(!state.dailyGuessLoading)setTimeout(()=>loadDailyGuess(),0);return}
 if(rt.error){if($('#dailyGuessWorldCopy'))$('#dailyGuessWorldCopy').textContent=`${label} historical player pool`;if($('#mysteryWorldText'))$('#mysteryWorldText').textContent=`${label} · challenge unavailable`;if($('#guessQuestionHistory'))$('#guessQuestionHistory').innerHTML=`<div class="daily-empty"><h3>Challenge unavailable</h3><p>${rt.error}</p></div>`;return}
 const range=rt.minSeason===rt.maxSeason?String(rt.maxSeason):`${rt.minSeason}–${rt.maxSeason}`;if($('#dailyGuessWorldCopy'))$('#dailyGuessWorldCopy').textContent=`Player ${round} of ${DAILY_GUESS_ROUNDS} · ${label} world · ${range} pool.`;if($('#mysteryWorldText'))$('#mysteryWorldText').textContent=`${label} · ${range} player pool${rt.poolCount?` · ${rt.poolCount} players`:''}${rt.testMode?' · TEST PLAYER':''}`;
 const reveal=$('#mysteryReveal'),visual=$('#mysteryVisual'),guessLayout=$('.daily-guess-layout'),mysteryCard=$('.mystery-player-card'),questionPanel=$('.guess-question-panel'),finalPanel=$('.final-guess-panel');
 const setPanelHeading=(panel,eyebrow,title)=>{if(!panel)return;const e=panel.querySelector('.panel-title .eyebrow'),h=panel.querySelector('.panel-title h2');if(e)e.textContent=eyebrow;if(h)h.textContent=title};
 if(rec.completed){
  guessLayout?.classList.add('completed');mysteryCard?.classList.add('completed');questionPanel?.classList.add('completed');finalPanel?.classList.add('completed');
  setPanelHeading(questionPanel,rec.solved?'HOW YOU SOLVED IT':'HOW IT ENDED','Your game recap.');setPanelHeading(finalPanel,'YOUR GUESSES',rec.solved?'Final attempts.':'Attempts used.');
  if(reveal){reveal.classList.remove('hidden');reveal.innerHTML=revealDailyMystery(rt,rec)+(round<DAILY_GUESS_ROUNDS?`<button id="nextDailyGuess" class="btn btn-primary btn-full guess-next-btn">NEXT PLAYER ${round+1}/${DAILY_GUESS_ROUNDS} →</button>`:`<button id="finishDailyGuess" class="btn btn-primary btn-full guess-next-btn">ALL 5 PLAYERS COMPLETE →</button>`)}
  if(visual)visual.classList.add('hidden');if($('#mysteryTitle'))$('#mysteryTitle').textContent=rec.solved?'Solved!':'Answer revealed';if($('#mysteryChallengeTag'))$('#mysteryChallengeTag').textContent=`${rec.solved?'CORRECT ✓':'REVEALED'} · ${round}/${DAILY_GUESS_ROUNDS}`;
  const next=$('#nextDailyGuess');

if(next) next.onclick=()=>{
  const nextRound=round+1;

  /* Always start the next player as a fresh challenge. */
  const root=dailyGameState(world);
  const nextKey=dailyGuessKey(isoToday(),nextRound);
  if(root?.guessByDate) delete root.guessByDate[nextKey];

  state.dailyGuessRound=nextRound;
  state.dailyGuessRuntime=null;
  state.dailyGuessSelected=null;
  state.dailyGuessLoading=false;

  clearTimeout(state.dailyGuessSearchTimer);

  const search=$('#dailyGuessSearch');
  if(search) search.value='';

  const suggestions=$('#dailyGuessSuggestions');
  if(suggestions) suggestions.innerHTML='';

  const selected=$('#dailyGuessSelected');
  if(selected){
    selected.innerHTML='';
    selected.classList.add('hidden');
  }

  const questionHistory=$('#guessQuestionHistory');
  if(questionHistory) questionHistory.innerHTML='<div class="data-empty">No questions asked yet.</div>';

  const guessHistory=$('#dailyGuessHistory');
  if(guessHistory) guessHistory.innerHTML='';

  const questionType=$('#guessQuestionType');
  if(questionType) questionType.selectedIndex=0;

  const questionValue=$('#guessQuestionValue');
  if(questionValue) questionValue.innerHTML='';

  save();
  loadDailyGuess();
};
}else{
  guessLayout?.classList.remove('completed');mysteryCard?.classList.remove('completed');questionPanel?.classList.remove('completed');finalPanel?.classList.remove('completed');
  setPanelHeading(questionPanel,'ASK A QUESTION','Narrow it down.');setPanelHeading(finalPanel,'FINAL GUESS','Name the player.');
  if(reveal)reveal.classList.add('hidden');if(visual)visual.classList.remove('hidden');if($('#mysteryTitle'))$('#mysteryTitle').textContent='Who is it?';if($('#mysteryChallengeTag'))$('#mysteryChallengeTag').textContent=`PLAYER ${round} OF ${DAILY_GUESS_ROUNDS}${rt.testMode?' · TEST':''}`
 }
 const history=$('#guessQuestionHistory');if(history)history.innerHTML=rec.questions.length?rec.questions.map((q,i)=>`<div class="guess-history-row"><span>${i+1}</span><b>${q.text}</b><strong class="${q.answer?'yes':'no'}">${q.answer?'YES':'NO'}</strong></div>`).join(''):`<div class="data-empty">${rec.completed?'No questions were needed.':'No questions asked yet.'}</div>`;
 const type=$('#guessQuestionType'),ask=$('#askGuessQuestion');if(type){type.disabled=rec.completed||rec.questions.length>=10;type.onchange=populateDailyQuestionValues}populateDailyQuestionValues();if($('#guessQuestionValue'))$('#guessQuestionValue').disabled=rec.completed||rec.questions.length>=10;if(ask){ask.disabled=rec.completed||rec.questions.length>=10;ask.onclick=askDailyQuestion}
 const guesses=$('#dailyGuessHistory');if(guesses)guesses.innerHTML=rec.guesses.length?`<div class="wrong-guess-title">${rec.completed?'FINAL GUESSES':'YOUR GUESSES'}</div>`+rec.guesses.map((g,i)=>`<div class="wrong-guess-row ${g.correct?'correct':''}"><span>${g.correct?'✓':'✕'}</span><div><b>${g.name}</b><small>Guess ${i+1}${g.school?' · '+g.school:''}${g.years?' · '+g.years:''}</small></div></div>`).join(''):(rec.completed?'<div class="data-empty">No final guesses were used.</div>':'');
 const input=$('#dailyGuessSearch'),submit=$('#submitDailyGuess'),selected=$('#dailyGuessSelected');if(input){input.disabled=rec.completed||rec.guesses.length>=3;input.oninput=()=>{state.dailyGuessSelected=null;if(selected)selected.classList.add('hidden');if(submit)submit.disabled=true;clearTimeout(state.dailyGuessSearchTimer);const q=input.value.trim();if(q.length<2){const w=$('#dailyGuessSuggestions');if(w)w.innerHTML='';return}state.dailyGuessSearchTimer=setTimeout(()=>searchDailyGuessPlayers(q),180)}}if(selected){if(state.dailyGuessSelected){selected.classList.remove('hidden');selected.innerHTML=`<b>${state.dailyGuessSelected.name}</b><span>${(state.dailyGuessSelected.schools||[state.dailyGuessSelected.school]).filter(Boolean).join(' · ')}</span>`}else selected.classList.add('hidden')}if(submit){submit.disabled=rec.completed||!state.dailyGuessSelected||rec.guesses.length>=3;submit.onclick=submitDailyPlayerGuess}
 if(done>=DAILY_GUESS_ROUNDS)dailyUpdateStreak(world);save();
}
function askDailyQuestion(){const rt=state.dailyGuessRuntime,rec=dailyGuessRecord();if(!rt?.answer||rec.completed||rec.questions.length>=10)return;const type=$('#guessQuestionType')?.value,value=$('#guessQuestionValue')?.value;if(!value)return;const key=`${type}|${value}`;if(rec.questions.some(q=>q.key===key)){toast('You already asked that question.');return}rec.questions.push({key,type,value,text:dailyQuestionText(type,value),answer:dailyQuestionAnswer(rt.answer,type,value)});save();renderDailyGuess()}
async function searchDailyGuessPlayers(q){const world=state.activeWorld,wrap=$('#dailyGuessSuggestions');if(!wrap)return;wrap.innerHTML='<div class="guess-search-loading">Searching historical player pool…</div>';const data=await jfetch(query('/api/guess-player/search',{division:world,q}),[],4000);if(state.activeWorld!==world)return;const items=(Array.isArray(data)?data:[]).slice(0,10);wrap.innerHTML=items.length?items.map((p,i)=>{const ys=(p.seasons||[]);const years=ys.length?`${ys[0]}${ys.length>1?'–'+ys[ys.length-1]:''}`:'';return `<button data-guess-result="${i}"><b>${p.name}</b><span>${(p.schools||[p.school]).filter(Boolean).join(' · ')}${years?' · '+years:''}</span></button>`}).join(''):'<div class="guess-search-loading">No players found in this world.</div>';$$('[data-guess-result]').forEach(b=>b.onclick=()=>{state.dailyGuessSelected=items[Number(b.dataset.guessResult)];wrap.innerHTML='';if($('#dailyGuessSearch'))$('#dailyGuessSearch').value=state.dailyGuessSelected.name;renderDailyGuess()})}
function submitDailyPlayerGuess(){const rt=state.dailyGuessRuntime,rec=dailyGuessRecord(),p=state.dailyGuessSelected;if(!rt?.answer||!p||rec.completed||rec.guesses.length>=3)return;const norm=x=>String(x||'').trim().toLowerCase().replace(/\s+/g,' '),correct=norm(p.name)===norm(rt.answer.name),ys=(p.seasons||[]),years=ys.length?`${ys[0]}${ys.length>1?'–'+ys[ys.length-1]:''}`:'';rec.guesses.push({id:p.id,name:p.name,school:(p.schools||[p.school]).filter(Boolean).join(' · '),years,correct});state.dailyGuessSelected=null;if(correct){rec.solved=true;rec.completed=true;rec.score=Math.max(20,100-rec.questions.length*4-(rec.guesses.length-1)*15);toast(`Correct! +${rec.score} pts`)}else if(rec.guesses.length>=3){rec.failed=true;rec.completed=true;rec.score=0;toast('No guesses left — player revealed.')}else toast(`${3-rec.guesses.length} guesses remaining.`);dailyUpdateStreak();save();renderDailyGuess()}

function renderDashboard(){
 renderProspects();
 renderWorldSelectors();
 const rows=$('#worldRoundRows');
 if(rows){rows.innerHTML=worldOrder.map(w=>`<div class="round-row"><div><b>${worlds[w].label}</b><small>${state.participation[w]?(state.lang==='pt'?'Jogando':state.lang==='es'?'Jugando':'Playing'):(state.lang==='pt'?'Opcional':state.lang==='es'?'Opcional':'Optional')}</small></div><div class="round-status"><b style="color:${state.participation[w]?'#12a06c':'#8091a0'}">${state.participation[w]?'ACTIVE':state.lang==='pt'?'Não jogando':state.lang==='es'?'No jugando':'Not playing'}</b></div><button class="round-toggle ${state.participation[w]?'leave':''}" data-world-toggle="${w}">${state.participation[w]?(state.lang==='pt'?'SAIR':state.lang==='es'?'SALIR':'LEAVE'):(state.lang==='pt'?'ENTRAR':state.lang==='es'?'JUGAR':'JOIN')}</button></div>`).join('');$$('#worldRoundRows [data-world-toggle]').forEach(b=>b.onclick=()=>toggleWorldParticipation(b.dataset.worldToggle));}
 const cfg=worlds[state.activeWorld];const sourceLabel=state.activeWorld.startsWith('D')?'NCAA.com':state.activeWorld==='NAIA'?'NAIA.org':'NJCAA.org';const worldNewsLabel={D1:'NCAA DIVISION I',D2:'NCAA DIVISION II',D3:'NCAA DIVISION III',NAIA:"NAIA MEN'S SOCCER",NJCAA1:'NJCAA DIVISION I'}[state.activeWorld]||cfg.label;if($('#newsWorldLabel'))$('#newsWorldLabel').textContent=worldNewsLabel;if($('#newsSourceLabel'))$('#newsSourceLabel').textContent=sourceLabel;if($('#newsSourceLink')){$('#newsSourceLink').href=cfg.source;$('#newsSourceLink').textContent=`OPEN ${sourceLabel.replace('.org','').replace('.com','')} ↗`}if($('#gamesOfficialSource'))$('#gamesOfficialSource').href=cfg.source;
 renderNews();if($('#pickGamesPreview'))renderPickPreview();renderScores();
}
function renderProspects(){
 const wrap=$('#prospectList');if(!wrap)return;
 const items=state.prospects||[];
 wrap.innerHTML=items.slice(0,5).map((p,i)=>`<div class="prospect-row"><span class="prospect-rank">${i+1}</span><div><b>${p.name}</b><small>${p.school}${p.conference?' · '+p.conference:''}</small></div><strong>${p.rating||p.overall||'—'}</strong></div>`).join('')||'<div class="fine">Promising players are loading…</div>';
}
async function loadProspects(){const w=state.activeWorld;const items=await jfetch(query('/api/prospects',{division:w,limit:5}),[],1800);if(state.activeWorld===w&&Array.isArray(items)){state.prospects=items;renderProspects();cacheDashboardWorld(w)}}
function renderNews(){
 const data=(state.news&&state.news.length?state.news:(fallbackNews[state.activeWorld]||[]));const filt=state.newsFilter;const filtered=filt==='all'?data:data.filter(n=>(n.category||'').toLowerCase().includes(filt));const shown=filtered.slice(0,3);
 if(!shown.length){$('#newsMosaic').innerHTML='<div class="data-empty"><b>No stories in this filter yet.</b><br>Use Refresh to check the official source.</div>';return}
 $('#newsMosaic').innerHTML=shown.map((n,i)=>`<a class="news-item ${i===0?'lead':''}" href="${n.url||worlds[state.activeWorld].source}" target="_blank" rel="noreferrer"><div class="news-item-bg" style="background-image:url('${n.image_url||''}')"></div><div class="news-content"><small>${n.source||worlds[state.activeWorld].label}${n.published_at?` · ${String(n.published_at).slice(0,10)}`:''}</small><h3>${n.title}</h3></div></a>`).join('')
}
function statusLower(g){return String(g?.status||'').toLowerCase()}
function isFinal(g){return statusLower(g).startsWith('final')||statusLower(g).startsWith('finished')||statusLower(g).startsWith('complete')}
function isLive(g){return statusLower(g).startsWith('live')}
function scheduled(g){return !isFinal(g)&&!isLive(g)}
function isoToday(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function isoOffset(days){const d=new Date();d.setDate(d.getDate()+Number(days||0));return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function gameTeamKey(s){
 let x=String(s||'').toLowerCase().replace(/&/g,' and ').replace(/[^a-z0-9]+/g,' ').trim();
 x=x.replace(/^umass\b/,'massachusetts').replace(/^fdu$/,'fairleigh dickinson').replace(/^florida gulf coast university\b/,'fgcu').replace(/^florida gulf coast\b/,'fgcu').replace(/^unc\b/,'north carolina').replace(/^nc state\b/,'north carolina state').replace(/^uc\b/,'california').replace(/^cal st\b/,'california state').replace(/^cal state\b/,'california state');
 x=x.replace(/^st\b/,'saint').replace(/\bst$/,'state').replace(/\bu$/,'university');
 x=x.replace(/\b(the|university|college|of|at)\b/g,' ');
 return x.replace(/[^a-z0-9]/g,'');
}
function gameKey(g){const pair=[gameTeamKey(g.home_team),gameTeamKey(g.away_team)].sort();return `${g.game_date}|${pair[0]}|${pair[1]}`}
function normalizeTeam(s){return gameTeamKey(s)}
function sourceReliability(g){const src=String(g?.source_name||'').toLowerCase();let score=0;if(src.includes('official'))score+=14;if(src.includes('ncaa'))score+=12;if(src.includes('verified'))score+=8;if(src.includes('snapshot'))score-=2;if(src.includes('prototype'))score-=12;if(g?.source_url)score+=3;if(isLive(g)||isFinal(g))score+=4;if(g?.start_time)score+=2;if(g?.home_score!=null||g?.away_score!=null)score+=2;return score}
function canonicalTeamName(name){const meta=teamMeta(name);return meta?.school||name}
function normalizeGameRow(g){const home=canonicalTeamName(g?.home_team),away=canonicalTeamName(g?.away_team);return {...g,home_team:home,away_team:away,home_conference:g?.home_conference||teamMeta(home)?.conference||'',away_conference:g?.away_conference||teamMeta(away)?.conference||''}}
function chooseBetterGame(a,b){return sourceReliability(b)>sourceReliability(a)?b:a}
function dedupeStateGames(){const best=new Map();for(const raw of state.games||[]){const g=normalizeGameRow(raw);if(!g?.game_date||!g?.home_team||!g?.away_team)continue;if(normalizeTeam(g.home_team)===normalizeTeam(g.away_team))continue;const key=gameKey(g);best.set(key,best.has(key)?chooseBetterGame(best.get(key),g):g)}state.games=[...best.values()]}
function mergeGames(items){const map=new Map((state.games||[]).map(g=>[gameKey(normalizeGameRow(g)),normalizeGameRow(g)]));(items||[]).forEach(raw=>{const g=normalizeGameRow(raw);const key=gameKey(g);map.set(key,map.has(key)?chooseBetterGame(map.get(key),g):g)});state.games=[...map.values()];dedupeStateGames()}
function replaceGameDate(date,items){state.games=(state.games||[]).filter(g=>g.game_date!==date);mergeGames(items||[]);dedupeStateGames()}
function teamMeta(name){const n=normalizeTeam(name);if(!n)return null;let best=null;for(const t of state.teamRows||[]){const vals=[t.school,t.abbreviation,t.ncaa_slug].filter(Boolean).map(normalizeTeam);if(vals.includes(n))return t;const school=normalizeTeam(t.school);if(n.length>4&&school.length>4&&(school.includes(n)||n.includes(school)))best=best||t}return best}
function teamMatches(gameName,school){if(!school||school==='all')return true;const a=normalizeTeam(gameName),b=normalizeTeam(school);if(a===b||a.includes(b)||b.includes(a))return true;const meta=teamMeta(gameName);return meta?normalizeTeam(meta.school)===b:false}
function gameConference(g,side){return (side==='home'?g.home_conference:g.away_conference)||teamMeta(side==='home'?g.home_team:g.away_team)?.conference||''}
function gameMatches(g,conf='all',school='all'){
 const schoolOk=school==='all'||teamMatches(g.home_team,school)||teamMatches(g.away_team,school);
 const confOk=conf==='all'||gameConference(g,'home')===conf||gameConference(g,'away')===conf;
 return schoolOk&&confOk
}
function nextGameForSchool(school){const today=isoToday();return state.games.filter(g=>scheduled(g)&&g.game_date>=today&&(teamMatches(g.home_team,school)||teamMatches(g.away_team,school))).sort((a,b)=>a.game_date.localeCompare(b.game_date)||(a.start_time||'').localeCompare(b.start_time||''))[0]||null}
function nextGameHtml(school){const g=nextGameForSchool(school);if(!g)return '<span class="next-game unavailable">NEXT GAME · schedule syncing / not yet verified</span>';const d=new Date(g.game_date+'T12:00:00');const label=d.toLocaleDateString(state.lang==='pt'?'pt-BR':state.lang==='es'?'es-ES':'en-US',{month:'short',day:'numeric'});const short=n=>teamMeta(n)?.abbreviation||n;return `<span class="next-game"><b>NEXT · ${label}</b> · ${short(g.home_team)} vs ${short(g.away_team)}</span>`}

function currentRoundGames(){
 const today=isoToday();const live=state.games.filter(isLive);if(live.length)return live.concat(state.games.filter(g=>g.game_date===today&&!isLive(g))).slice(0,5);
 const todayGames=state.games.filter(g=>g.game_date===today);if(todayGames.length)return todayGames.slice(0,5);
 const upcoming=state.games.filter(g=>scheduled(g)&&g.game_date>=today).sort((a,b)=>a.game_date.localeCompare(b.game_date)||(a.start_time||'').localeCompare(b.start_time||''));
 if(upcoming.length){const first=upcoming[0].game_date;const same=upcoming.filter(g=>g.game_date===first);return same.slice(0,5)}
 const finals=state.games.filter(isFinal).sort((a,b)=>b.game_date.localeCompare(a.game_date));if(finals.length){const latest=finals[0].game_date;return finals.filter(g=>g.game_date===latest).slice(0,5)}return []
}
function renderPickPreview(){const wrap=$('#pickGamesPreview');if(!wrap)return;const games=state.games.filter(scheduled).sort((a,b)=>a.game_date.localeCompare(b.game_date)||(a.start_time||'').localeCompare(b.start_time||'')).slice(0,1);const preds=state.predictions[state.activeWorld]||{};wrap.innerHTML=games.map(g=>{const p=preds[g.id]||{h:'',a:''};return`<div class="pick-game"><small>${g.game_date}${g.start_time?' · '+g.start_time:''} · SCHEDULED</small><div class="pick-row"><span>${g.home_team}</span><input data-prev-home="${g.id}" type="number" min="0" value="${p.h}"><span>×</span><input data-prev-away="${g.id}" type="number" min="0" value="${p.a}"><span>${g.away_team}</span></div></div>`}).join('')||'<div class="fine">Upcoming games are loading from the 2026 schedule.</div>'}
function renderScores(){const wrap=$('#dashGames');if(!wrap)return;const today=isoToday();const allToday=state.games.filter(g=>g.game_date===today).sort((a,b)=>gameStartMinutes(a.start_time)-gameStartMinutes(b.start_time));const games=[...allToday.filter(isLive),...allToday.filter(g=>!isLive(g))].slice(0,5);wrap.innerHTML=games.map(g=>{const live=isLive(g),final=isFinal(g),hasScore=g.home_score!=null&&g.away_score!=null,scoreVisible=live||final||hasScore;const when=live?(g.status||'LIVE'):(final||hasScore?'FINAL':(g.start_time||'TODAY'));return`<button class="dash-score-card ${live?'live-row':''}" data-score-date="${g.game_date}"><div class="dash-score-top"><span>${live?'<b class="live-mini">● LIVE</b>':when}</span><span>${g.start_time||''}</span></div><div class="dash-team-row"><b>${g.home_team}</b><strong>${scoreVisible?(g.home_score??'–'):''}</strong></div><div class="dash-team-row"><b>${g.away_team}</b><strong>${scoreVisible?(g.away_score??'–'):''}</strong></div></button>`}).join('')||'<div class="fine">No verified games are cached for today yet. Live data refreshes in the background.</div>';$$('[data-score-date]').forEach(b=>b.onclick=()=>{state.gameDate=b.dataset.scoreDate;save();show('games');renderGames()})}
async function refreshScoreboardPreview(force=false){if(!['D1','D2','D3'].includes(state.activeWorld))return;const w=state.activeWorld;const items=await jfetch(query('/api/scoreboard-preview',{division:w,refresh:force?1:0}),[]);if(state.activeWorld!==w)return;if(Array.isArray(items)&&items.length){replaceGameDate(isoToday(),items);renderScores();renderPickPreview();cacheDashboardWorld(w);if($('.page.active')?.id==='games')renderGames()}}
async function refreshNewsLive(force=false,notify=false){if(!['D1','D2','D3','NAIA','NJCAA1'].includes(state.activeWorld))return;const w=state.activeWorld;const items=await jfetch(query('/api/news',{division:w,limit:30,refresh:force?1:0}),[]);if(state.activeWorld!==w)return;if(Array.isArray(items)&&items.length){state.news=items;renderNews();cacheDashboardWorld(w);if(notify)toast('Current official news updated.')}}
async function reloadGamesOnly(){const since=isoOffset(-7),until=isoOffset(45);const [games,cov,filters]=await Promise.all([jfetch(query('/api/games',{division:state.activeWorld,since,until}),[]),jfetch(query('/api/game-coverage',{division:state.activeWorld}),state.gameCoverage||{}),jfetch(query('/api/filters',{division:state.activeWorld}),{conferences:[],schools:[],teams:[]})]);if(Array.isArray(games))state.games=games;state.gameCoverage=cov;if(filters){state.teamRows=filters.teams||state.teamRows;state.filters={conferences:filters.conferences||[],schools:filters.schools||[]}}buildFilters();if($('.page.active')?.id==='dashboard')renderDashboard();if($('.page.active')?.id==='games')renderGames();if($('.page.active')?.id==='market')renderMarket();if($('#predictionRows')){predictionFilterOptions();renderPredictionRows()}}
async function refreshUpcomingGamesFast(force=false){const w=state.activeWorld;if(!['D1','D2','D3'].includes(w))return;const payload=await jfetch(query('/api/upcoming-games',{division:w,days:45,refresh:force?1:0}),null);if(state.activeWorld!==w||!payload)return;const games=Array.isArray(payload.games)?payload.games:[];if(games.length){mergeGames(games);renderScores();renderPickPreview();cacheDashboardWorld(w);if($('.page.active')?.id==='market')renderMarket();if($('.page.active')?.id==='team')renderTeam();if($('.page.active')?.id==='games')renderGames()}}
async function ensureSeasonGames(){return false;}
function predictionFilterOptions(){
 const confSel=$('#predConference'),schoolSel=$('#predSchool');if(!confSel||!schoolSel)return;
 const oldC=state.predConference||'all';const oldS=state.predSchool||'all';
 const gameConfs=state.games.flatMap(g=>[g.home_conference,g.away_conference]).filter(Boolean);const confs=[...new Set([...(state.teamRows||[]).map(t=>t.conference).filter(Boolean),...gameConfs])].sort();confSel.innerHTML=optionHtml('all',tr('allConferences'))+confs.map(x=>optionHtml(x)).join('');confSel.value=confs.includes(oldC)?oldC:'all';state.predConference=confSel.value;
 const schools=[];(state.teamRows||[]).filter(t=>state.predConference==='all'||t.conference===state.predConference).forEach(t=>t.school&&schools.push(t.school));state.games.forEach(g=>{if(state.predConference==='all'||gameConference(g,'home')===state.predConference)g.home_team&&schools.push(g.home_team);if(state.predConference==='all'||gameConference(g,'away')===state.predConference)g.away_team&&schools.push(g.away_team)});const unique=[...new Set(schools)].sort();schoolSel.innerHTML=optionHtml('all',tr('allSchools'))+unique.map(x=>optionHtml(x)).join('');schoolSel.value=unique.includes(oldS)?oldS:'all';state.predSchool=schoolSel.value;
}
function capturePredictionInputs(){state.predictions[state.activeWorld]=state.predictions[state.activeWorld]||{};$$('[data-modal-home]').forEach(h=>{const a=$(`[data-modal-away="${h.dataset.modalHome}"]`);if(a)state.predictions[state.activeWorld][h.dataset.modalHome]={h:h.value,a:a.value}});save()}
function predictionGames(){return state.games.filter(g=>scheduled(g)&&g.game_date>=isoToday()&&gameMatches(g,state.predConference,state.predSchool)).sort((a,b)=>a.game_date.localeCompare(b.game_date)||(a.start_time||'').localeCompare(b.start_time||''))}
function renderPredictionRows(){
 const wrap=$('#predictionRows');if(!wrap)return;const preds=state.predictions[state.activeWorld]||{};const games=predictionGames();const pages=Math.max(1,Math.ceil(games.length/state.predPageSize));state.predPage=clamp(state.predPage,1,pages);const start=(state.predPage-1)*state.predPageSize;const shown=games.slice(start,start+state.predPageSize);
 wrap.innerHTML=shown.map(g=>{const p=preds[g.id]||{h:'',a:''};return`<div class="prediction-game-row"><span class="when">${g.game_date}${g.start_time?'<br>'+g.start_time:''}</span><b>${g.home_team}</b><input data-modal-home="${g.id}" type="number" min="0" value="${p.h}"><span>×</span><input data-modal-away="${g.id}" type="number" min="0" value="${p.a}"><b class="away">${g.away_team}</b><span class="status">UPCOMING</span></div>`}).join('')||'<div class="data-empty">No upcoming verified games match these filters yet.</div>';
 const pg=$('#predictionPaging');if(pg){const from=games.length?start+1:0,to=Math.min(start+state.predPageSize,games.length);let nums=[];for(let n=Math.max(1,state.predPage-2);n<=Math.min(pages,state.predPage+2);n++)nums.push(n);pg.innerHTML=`<span>${tr('predShowing')} ${from}–${to} of ${games.length} ${tr('ofGames')}</span><div class="pred-page-buttons"><button data-pred-page="${Math.max(1,state.predPage-1)}" ${state.predPage===1?'disabled':''}>‹</button>${nums.map(n=>`<button class="${n===state.predPage?'active':''}" data-pred-page="${n}">${n}</button>`).join('')}<button data-pred-page="${Math.min(pages,state.predPage+1)}" ${state.predPage===pages?'disabled':''}>›</button></div>`;$$('[data-pred-page]').forEach(b=>b.onclick=()=>{capturePredictionInputs();state.predPage=Number(b.dataset.predPage)||1;renderPredictionRows()})}
 const syncNote=$('#predictionSyncNote');if(syncNote)syncNote.textContent=state.seasonSyncing[state.activeWorld]?'Loading the complete 2026 schedule…':`${games.length} upcoming verified games available`;
}
function openPredictions(){
 state.predPage=1;
 openModal(`<div class="eyebrow">PICK'EM · ${worlds[state.activeWorld].label}</div><h2>${tr('roundPredictions')}</h2><p>${tr('predictCopy')}</p><div class="prediction-filter-bar"><select id="predConference"></select><select id="predSchool"></select></div><div id="predictionSyncNote" class="prediction-sync-note"></div><div id="predictionRows" class="prediction-list games-style"></div><div id="predictionPaging" class="prediction-pagination"></div><button id="savePredModal" class="btn btn-primary btn-full" style="margin-top:14px">${tr('savePredictions')}</button>`);$('#modal .modal-card').classList.add('prediction-modal');predictionFilterOptions();renderPredictionRows();
 $('#predConference').onchange=e=>{capturePredictionInputs();state.predConference=e.target.value;state.predSchool='all';state.predPage=1;predictionFilterOptions();renderPredictionRows()};$('#predSchool').onchange=e=>{capturePredictionInputs();state.predSchool=e.target.value;const meta=(state.teamRows||[]).find(t=>t.school===state.predSchool);if(meta?.conference){state.predConference=meta.conference;predictionFilterOptions()}state.predPage=1;renderPredictionRows()};
 $('#savePredModal').onclick=()=>{capturePredictionInputs();closeModal();renderPickPreview();toast('Predictions saved.')}
}
function savePreview(){state.predictions[state.activeWorld]=state.predictions[state.activeWorld]||{};$$('[data-prev-home]').forEach(h=>{const id=h.dataset.prevHome,a=$(`[data-prev-away="${id}"]`);state.predictions[state.activeWorld][id]={h:h.value,a:a.value}});save();toast(tr('savePredictions'))}
function renderWorldTabs(){$('#lineupWorldTabs').innerHTML=worldOrder.map(w=>`<button class="world-tab ${w===state.activeWorld?'active':''}" data-lineup-world="${w}">${worlds[w].label}<small>${money(worlds[w].budget)}</small></button>`).join('');$$('[data-lineup-world]').forEach(b=>b.onclick=()=>{show('team');loadWorld(b.dataset.lineupWorld).then(()=>{if($('.page.active')?.id==='team')renderTeam()})})}
function formationSlots(form){const counts=formations[form];const slots=[];Object.entries(counts).forEach(([p,n])=>{for(let i=0;i<n;i++)slots.push({pos:p,index:i})});return slots}
function getStarterByPos(pos,index){const ids=ws().lineup.starters;const players=ids.map(id=>state.players.find(p=>p.id===id)).filter(Boolean).filter(p=>p.position===pos);return players[index]||null}
function pitchCoords(form){
 const c=formations[form];const spread=(n,y,min=24,max=76)=>Array.from({length:n},(_,i)=>({x:n===1?50:min+((max-min)*i/(n-1)),y}));
 return{FW:spread(c.FW,24,25,75),MF:spread(c.MF,49,20,80),DF:spread(c.DF,72,18,82),GK:spread(1,89)}
}
function renderTeam(){
 renderWorldTabs(); const s=ws();
 $('#formationButtons').innerHTML=Object.keys(formations).map(f=>`<button class="formation-btn ${f===s.formation?'active':''}" data-formation="${f}">${f}</button>`).join('');$$('[data-formation]').forEach(b=>b.onclick=()=>{s.formation=b.dataset.formation;s.lineup.starters=[];save();renderTeam();renderMarket()});
 const count=s.lineup.starters.length; const cost=spent(); const remain=available();
 $('#sumBase').textContent=money(baseBudget());$('#sumSpent').textContent=money(cost);$('#sumRemain').textContent=money(remain);$('#sumAvg').textContent=money(totalBudget()/11);$('[data-i18n="playersSelected"]').textContent=`Players (${count}/11)`;
 $('#confirmTeam').disabled=!(count===11&&s.lineup.HC&&s.lineup.AC&&remain>=0);
 const coords=pitchCoords(s.formation);let html='';for(const pos of ['FW','MF','DF','GK']){coords[pos].forEach((xy,i)=>{const p=getStarterByPos(pos,i);html+=`<button class="pitch-slot ${p?'selected-player':'empty'}" style="left:${xy.x}%;top:${xy.y}%" data-slot-pos="${pos}" data-slot-index="${i}" ${p?`data-player-id="${p.id}"`:''}>${p?`<div class="jersey">👕</div><b>${p.name.split(' ').slice(-1)[0]}</b><small>${money(p.price)}</small>`:`<div class="plus">+</div><b>${pos}</b>`}</button>`})}$('#pitchSlots').innerHTML=html;
 $$('.pitch-slot').forEach(b=>b.onclick=()=>{if(b.dataset.playerId)openPlayerDetails(b.dataset.playerId);else openMarketFor('players',b.dataset.slotPos,false)});
 const hc=state.coaches.find(c=>c.id===s.lineup.HC),ac=state.coaches.find(c=>c.id===s.lineup.AC);$('#coachSlots').innerHTML=`${coachChip('HC',hc)}${coachChip('AC',ac)}`;$$('[data-coach-slot]').forEach(b=>b.onclick=()=>{const role=b.dataset.coachSlot==='HC'?'Head Coach':'Assistant Coach';openMarketFor(role,'all',false)});$$('[data-remove-coach-slot]').forEach(b=>b.onclick=e=>{e.stopPropagation();const code=b.dataset.removeCoachSlot;if(code==='HC')s.lineup.HC=null;else s.lineup.AC=null;save();renderTeam();renderMarket()});
 renderBenchCards();renderRoster();
}
function coachChip(code,c){return`<div class="coach-chip"><button class="coach-select" data-coach-slot="${code}"><span>${code}</span><div><small>${code==='HC'?'HEAD COACH':'ASSISTANT COACH'}</small><b>${c?`${c.name} · ${money(c.price)}`:'Click to select'}</b></div></button>${c?`<button class="coach-remove" title="Remove ${code}" data-remove-coach-slot="${code}">×</button>`:'<span></span>'}</div>`}
function renderBenchCards(){const b=ws().lineup.bench||{};$('#benchCards').innerHTML=['GK','DF','MF','FW'].map(pos=>{const p=state.players.find(x=>x.id===b[pos]);return`<button class="bench-mini" data-bench-pos="${pos}"><span class="mini-shirt">👕</span><div><small>${pos}</small><b>${p?p.name.split(' ').slice(-1)[0]:'Optional'}</b>${p?`<small>${money(p.price)}</small>`:''}</div></button>`}).join('');$$('[data-bench-pos]').forEach(btn=>btn.onclick=()=>openMarketFor('players',btn.dataset.benchPos,true))}
function rowFor(pos,p,coach=false){return`<div class="roster-row"><span><span class="roster-pos">${pos}</span></span><span class="${p?'roster-name':'roster-empty'}">${p?p.name:'Empty position'}</span><span>${p?p.school:'—'}</span><span>${p?p.conference||'—':'—'}</span><span>${p?money(p.price):'—'}</span><span>${p?`<button class="remove-btn" data-remove="${p.id}" data-coach="${coach?'1':'0'}">•••</button>`:''}</span></div>`}
function renderRoster(){const s=ws();let out='';for(const pos of ['GK','DF','MF','FW']){const n=formations[s.formation][pos];for(let i=0;i<n;i++)out+=rowFor(pos,getStarterByPos(pos,i))}out+=rowFor('HC',state.coaches.find(c=>c.id===s.lineup.HC),true);out+=rowFor('AC',state.coaches.find(c=>c.id===s.lineup.AC),true);$('#rosterTable').innerHTML=out;$('#benchTable').innerHTML=['GK','DF','MF','FW'].map(pos=>rowFor(pos,state.players.find(p=>p.id===s.lineup.bench[pos]))).join('');$$('[data-remove]').forEach(b=>b.onclick=()=>{if(b.dataset.coach==='1')removeCoach(b.dataset.remove);else removePlayer(b.dataset.remove)})}
function removePlayer(id){const l=ws().lineup;l.starters=l.starters.filter(x=>x!==id);Object.keys(l.bench).forEach(k=>{if(l.bench[k]===id)delete l.bench[k]});save();renderTeam();renderMarket()}
function removeCoach(id){const l=ws().lineup;if(l.HC===id)l.HC=null;if(l.AC===id)l.AC=null;save();renderTeam();renderMarket()}

function marketEntity(){return $('#filterEntity')?.value||'players'}
function positionName(pos){return {GK:'Goalkeeper',DF:'Defender',MF:'Midfielder',FW:'Forward'}[pos]||'Player'}
function valuationDelta(p){const id=Number(String(p.id||'').replace(/\D/g,''))||0;const perf=(Number(p.goals||0)*.08)+(Number(p.assists||0)*.05)+(Number(p.minutes||0)>500?.18:0);const swing=(((id*37)%13)-6)/10;return Math.max(-0.9,Math.min(1.2,Number((swing+perf).toFixed(1))))}
function openMarketFor(entity='players',position='all',bench=false){state.marketContext={type:entity,position,bench};state.marketVisibleCount=60;if($('#filterEntity'))$('#filterEntity').value=entity;if($('#filterPos'))$('#filterPos').value=entity==='players'?position:'all';show('market');refreshMarketDependentFilters();renderMarket();setTimeout(()=>ensureMarketData(entity,entity==='players'?position:'all'),0)}
function renderMiniLineup(){const wrap=$('#miniPitchSlots');if(!wrap)return;const s=ws(),coords=pitchCoords(s.formation);let html='';for(const pos of ['FW','MF','DF','GK'])coords[pos].forEach((xy,i)=>{const p=getStarterByPos(pos,i);const focus=state.marketContext?.position===pos&&!p;html+=`<button class="mini-slot ${focus?'focus':''}" style="left:${xy.x}%;top:${xy.y}%" data-mini-pos="${pos}"><span>${p?p.name.split(' ').slice(-1)[0]:pos}</span></button>`});wrap.innerHTML=html;$('#miniLineupTitle').textContent=s.formation;const hc=state.coaches.find(c=>c.id===s.lineup.HC),ac=state.coaches.find(c=>c.id===s.lineup.AC);$('#miniCoachSlots').innerHTML=`<span>HC ${hc?hc.name.split(' ').slice(-1)[0]:'+'}</span><span>AC ${ac?ac.name.split(' ').slice(-1)[0]:'+'}</span>`;$$('[data-mini-pos]').forEach(b=>b.onclick=()=>openMarketFor('players',b.dataset.miniPos,false))}
function renderMarket(){
 renderWorldSelectors();renderMiniLineup();if($('#marketEyebrow'))$('#marketEyebrow').textContent=`${worlds[state.activeWorld].label} · 2026`;if($('#budgetLabel'))$('#budgetLabel').textContent=available().toFixed(1);if($('#boostBudgetHint'))$('#boostBudgetHint').textContent=`+${Number(ws().boost||0).toFixed(1)}M boost`;
 const entity=marketEntity(),pos=$('#filterPos').value,conf=$('#filterConf').value,school=$('#filterSchool').value,cls=$('#filterClass').value,q=$('#filterSearch').value.trim().toLowerCase(),sort=$('#filterSort').value;
 const title=entity==='players'?(pos==='all'?'Select a Player':`Select a ${positionName(pos)}`):`Select ${entity==='Head Coach'?'a Head Coach':'an Assistant Coach'}`;if($('#marketTitleDynamic'))$('#marketTitleDynamic').textContent=title;if($('#marketSubtitleDynamic'))$('#marketSubtitleDynamic').textContent=state.marketContext?.bench?'Choose an eligible reserve for your bench.':'Choose an option to add to your lineup.';
 if(entity==='players'&&!state.rosterLoaded&&state.players.length===0){
  if($('#marketCount'))$('#marketCount').textContent='Loading player roster…';
  $('#marketGrid').innerHTML='<div class="data-loading"><b>Loading players…</b><br>The roster is being read from the local verified database.</div>';
  ensureRosterLoaded().then(()=>{if($('.page.active')?.id==='market')renderMarket()});
  return;
 }
 let data=entity==='players'?state.players:state.coaches.filter(c=>entity==='Head Coach'?c.role==='Head Coach':c.role!=='Head Coach');
 data=data.filter(x=>(entity!=='players'||pos==='all'||x.position===pos)&&(conf==='all'||x.conference===conf)&&(school==='all'||x.school===school)&&(cls==='all'||entity!=='players'||classNorm(x.class_year)===cls)&&(!q||(x.name+' '+x.school).toLowerCase().includes(q)));
 data.sort((a,b)=>sort==='price_asc'?a.price-b.price:sort==='price_desc'?b.price-a.price:sort==='minutes'?(b.minutes||0)-(a.minutes||0):displayOverall(b)-displayOverall(a));
 const total=data.length,limit=Math.max(60,Number(state.marketVisibleCount||60)),shown=data.slice(0,limit);const cov=state.statsCoverage;const covText=entity==='players'&&cov?` · verified stats ${cov.players_with_verified_stats||0}/${cov.players||state.players.length}${cov.running?' · syncing…':''}`:'';
 if($('#marketCount'))$('#marketCount').textContent=`Showing ${shown.length} of ${total} ${entity==='players'?'players':'coaches'}${covText}`;
 let html=shown.map(x=>entity==='players'?playerCard(x):coachCard(x)).join('');if(!html)html=state.marketLoading?'<div class="data-empty"><b>Loading available players…</b><br>The market is opening without blocking the rest of the app.</div>':'<div class="data-empty"><b>No matching records.</b><br>Change the filters or refresh official data.</div>';if(total>shown.length)html+=`<div class="market-load-more"><button id="marketLoadMore" class="btn btn-soft">LOAD ${Math.min(60,total-shown.length)} MORE</button><span>${total-shown.length} remaining</span></div>`;$('#marketGrid').innerHTML=html;
 $$('[data-add-player]').forEach(b=>b.onclick=e=>{e.stopPropagation();addPlayer(b.dataset.addPlayer)});$$('[data-remove-player]').forEach(b=>b.onclick=e=>{e.stopPropagation();removePlayer(b.dataset.removePlayer)});$$('[data-add-coach]').forEach(b=>b.onclick=e=>{e.stopPropagation();addCoach(b.dataset.addCoach)});$$('[data-remove-coach]').forEach(b=>b.onclick=e=>{e.stopPropagation();removeCoach(b.dataset.removeCoach)});$$('[data-player-details]').forEach(b=>b.onclick=()=>openPlayerDetails(b.dataset.playerDetails));const more=$('#marketLoadMore');if(more)more.onclick=()=>{state.marketVisibleCount=limit+60;renderMarket()}
}
function avatarHtml(p){const initials=(p.name||'?').split(/\s+/).filter(Boolean).map(x=>x[0]).slice(0,2).join('').toUpperCase();return `<div class="player-avatar standardized-avatar">${initials}</div>`}
function statText(v){return v===null||v===undefined?'—':v}
function nextGameData(school){const g=nextGameForSchool(school);if(!g)return null;const opponent=teamMatches(g.home_team,school)?g.away_team:g.home_team;const away=teamMatches(g.away_team,school);const d=new Date(g.game_date+'T12:00:00');return{g,opponent,label:`${away?'@':'vs'} ${opponent}`,date:d.toLocaleDateString(state.lang==='pt'?'pt-BR':state.lang==='es'?'es-ES':'en-US',{month:'short',day:'numeric'})}}
function selectedCoachIds(){const l=ws().lineup;return [l.HC,l.AC].filter(Boolean)}
function playerCard(p){const delta=valuationDelta(p),next=nextGameData(p.school),up=delta>0,down=delta<0,selected=selectedPlayerIds().includes(p.id),action=selected?`<button class="btn add-v8 remove-v8" data-remove-player="${p.id}">REMOVE</button>`:`<button class="btn add-v8" data-add-player="${p.id}">ADD</button>`;return`<article class="player-card-v8 ${selected?'is-selected':''}" data-player-details="${p.id}"><div class="player-main-cell">${avatarHtml(p)}<div class="player-info"><b>${p.name}</b><span>${p.position} · ${p.school}</span><span>${p.conference||'—'}</span></div></div><div class="market-ovr">${displayOverall(p)}</div><div class="market-price">C$ ${Number(p.price).toFixed(1)}M</div><div class="market-var ${up?'up':down?'down':''}">${up?'▲':down?'▼':'—'} ${Math.abs(delta).toFixed(1)}M</div><div class="market-next"><b>${next?next.label:'Schedule pending'}</b><span>${next?next.date:''}</span></div>${action}</article>`}
function coachCard(c){const delta=valuationDelta(c),next=nextGameData(c.school),selected=selectedCoachIds().includes(c.id),action=selected?`<button class="btn add-v8 remove-v8" data-remove-coach="${c.id}">REMOVE</button>`:`<button class="btn add-v8" data-add-coach="${c.id}">ADD</button>`;return`<article class="player-card-v8 coach-card-v8 ${selected?'is-selected':''}"><div class="player-main-cell"><div class="player-avatar standardized-avatar">${(c.name||'?').split(/\s+/).filter(Boolean).map(x=>x[0]).slice(0,2).join('').toUpperCase()}</div><div class="player-info"><b>${c.name}</b><span>${c.role} · ${c.school}</span><span>${c.conference||'—'}</span></div></div><div class="market-ovr">${displayOverall(c)}</div><div class="market-price">C$ ${Number(c.price).toFixed(1)}M</div><div class="market-var ${delta>0?'up':delta<0?'down':''}">${delta>0?'▲':delta<0?'▼':'—'} ${Math.abs(delta).toFixed(1)}M</div><div class="market-next"><b>${next?next.label:'Schedule pending'}</b><span>${next?next.date:''}</span></div>${action}</article>`}
function openPlayerDetails(id){const p=state.players.find(x=>x.id===id);if(!p)return;const d=valuationDelta(p),next=nextGameData(p.school),selected=selectedPlayerIds().includes(p.id),action=selected?`<button class="btn add-v8 remove-v8" data-detail-remove="${p.id}">REMOVE FROM TEAM</button>`:`<button class="btn btn-primary" data-detail-add="${p.id}">ADD TO LINEUP</button>`;openModal(`<div class="player-detail-v8"><div class="detail-hero">${avatarHtml(p)}<div><div class="eyebrow">${p.position} · ${p.conference||'—'}</div><h2>${p.name}</h2><p>${p.school} · ${classNorm(p.class_year)}</p></div></div><div class="detail-kpis"><div><small>Overall</small><b>${displayOverall(p)}</b></div><div><small>Price</small><b>C$ ${Number(p.price).toFixed(1)}M</b></div><div><small>Season Points</small><b>${p.points!=null?Number(p.points).toFixed(1):'—'} pts</b></div><div><small>Value Change</small><b class="${d>0?'green-text':''}">${d>0?'▲ ':d<0?'▼ ':''}${Math.abs(d).toFixed(1)}M</b></div></div><h3>2026 Season</h3><div class="detail-stats"><span>Games <b>${statText(p.games)}</b></span><span>Starts <b>${statText(p.starts)}</b></span><span>Minutes <b>${p.minutes==null?'—':Math.round(p.minutes)}</b></span><span>Goals <b>${statText(p.goals)}</b></span><span>Assists <b>${statText(p.assists)}</b></span><span>Saves <b>${statText(p.saves)}</b></span></div><div class="detail-next"><small>NEXT MATCH</small><b>${next?next.label:'Schedule pending'}</b><span>${next?next.date:''}</span></div><div class="detail-actions">${p.source_url?`<a class="btn btn-outline" href="${p.source_url}" target="_blank" rel="noreferrer">OFFICIAL PLAYER/SCHOOL SOURCE ↗</a>`:''}${action}</div></div>`);setTimeout(()=>{const add=$('[data-detail-add]');if(add)add.onclick=()=>{addPlayer(add.dataset.detailAdd);closeModal()};const rem=$('[data-detail-remove]');if(rem)rem.onclick=()=>{removePlayer(rem.dataset.detailRemove);closeModal()}},0)}
function addPlayer(id){const p=state.players.find(x=>x.id===id);if(!p)return;const l=ws().lineup;if(selectedPlayerIds().includes(id)){toast('Already selected.');return}if(available()<p.price){toast('Not enough budget.');return}const need=formations[ws().formation][p.position];const current=l.starters.map(id=>state.players.find(x=>x.id===id)).filter(x=>x&&x.position===p.position).length;if(state.marketContext?.bench){if(l.bench[p.position]){toast('That bench position is already filled.');return}const starters=l.starters.map(id=>state.players.find(x=>x.id===id)).filter(x=>x&&x.position===p.position);if(starters.length<need){toast('Complete the starters in this position first.');return}const cheapest=Math.min(...starters.map(x=>x.price));if(p.price>cheapest){toast('Bench player must cost no more than the cheapest starter at that position.');return}l.bench[p.position]=id;toast(`${p.name} added to bench.`)}else if(current<need){l.starters.push(id);toast(`${p.name} added to lineup.`)}else if(!l.bench[p.position]){const cheapest=Math.min(...l.starters.map(id=>state.players.find(x=>x.id===id)).filter(x=>x&&x.position===p.position).map(x=>x.price));if(p.price<=cheapest){l.bench[p.position]=id;toast(`${p.name} added to bench.`)}else{toast('Bench player must cost no more than the cheapest starter at that position.');return}}else{toast('No open slot for this position.');return}save();renderTeam();renderMarket()}
function addCoach(id){const c=state.coaches.find(x=>x.id===id);if(!c)return;if(available()<c.price){toast('Not enough budget.');return}const l=ws().lineup;if(c.role==='Head Coach')l.HC=id;else l.AC=id;save();renderTeam();renderMarket();toast(`${c.name} selected.`)}

function renderBoost(){const packs=[{m:5,label:'Standard Boost',note:'Everyday flexibility'},{m:12,label:'Popular Boost',note:'+20% launch bonus',popular:true},{m:28,label:'Power Pack',note:'+40% strategy room'},{m:62,label:'Max Pack',note:'Maximum prototype budget'}];$('#boostTotal').textContent=Number(ws().boost||0).toFixed(1);$('#boostGrid').innerHTML=packs.map(p=>`<div class="boost-card ${p.popular?'popular':''}"><div class="boost-orb">M</div><h3>+${p.m}M</h3><p>${p.label}<br>${p.note}</p><button class="btn ${p.popular?'btn-primary':'btn-soft'} btn-full" data-boost="${p.m}">SELECT BENEFIT</button></div>`).join('');$$('[data-boost]').forEach(b=>b.onclick=()=>{ws().boost+=Number(b.dataset.boost);save();renderBoost();renderDashboard();renderTeam();renderMarket();toast('Budget boost activated.')})}

function rankingKey(world,cat,conf='all'){return `${world}|${cat}|${conf}`}
function snapshotFor(world,cat){return verifiedRankingSnapshots[world]?.[cat]||null}
function rankingRemoteData(world,cat,conf='all'){return state.rankingRemote[rankingKey(world,cat,conf)]||[]}
function rankingBaseConferences(world){
 const found=[...(state.rankingConferences[world]||[])];
 const snap=verifiedRankingSnapshots[world]||{};
 Object.values(snap).forEach(group=>(group.items||[]).forEach(x=>x.conference&&found.push(x.conference)));
 Object.entries(state.rankingRemote).filter(([k])=>k.startsWith(world+'|')).flatMap(([,v])=>v||[]).forEach(x=>x?.conference&&found.push(x.conference));
 const local=world===state.activeWorld?state.players:[];local.forEach(x=>x.conference&&found.push(x.conference));
 return [...new Set(found.filter(Boolean))].sort((a,b)=>a.localeCompare(b));
}
async function fetchRankingConferences(world,force=false){
 if(!force&&Object.prototype.hasOwnProperty.call(state.rankingConferences,world))return false;
 const data=await jfetch(query('/api/ranking-conferences',{division:world}),[]);
 state.rankingConferences[world]=Array.isArray(data)?data:[];
 return true;
}
function renderRankingConferenceOptions(){const sel=$('#standingConf');if(!sel)return;const old=sel.value||'all';const confs=rankingBaseConferences(state.rankingWorld);sel.innerHTML=optionHtml('all',tr('allConferences'))+confs.map(x=>optionHtml(x)).join('');sel.value=confs.includes(old)?old:'all'}
function normalizeRemoteRanking(cat,items){return (items||[]).map((x,i)=>({...x,rank:x.rank||i+1,goals:Number(x.goals||0),assists:Number(x.assists||0),shutouts:Number(x.shutouts||0),minutes:x.minutes==null?null:Number(x.minutes),verified:true}))}
async function fetchRankingRemote(world,cat,conf='all',force=false){
 if(cat==='fantasy')return false;const key=rankingKey(world,cat,conf);if(state.rankingLoading[key])return false;if(!force&&Object.prototype.hasOwnProperty.call(state.rankingRemote,key))return false;
 state.rankingLoading[key]=true;
 try{
   const endpoint=cat==='standings'?'/api/standings':'/api/ranking-category';
   const params=cat==='standings'?{division:world,conference:conf}:{division:world,category:cat,conference:conf};
   const data=await jfetch(query(endpoint,params),[]);
   state.rankingRemote[key]=normalizeRemoteRanking(cat,Array.isArray(data)?data:[]);
   return true;
 }finally{delete state.rankingLoading[key]}
}
function rankData(world,cat,conf='all'){
 if(cat==='fantasy'){const names=['SoccerKing23','GoalMachine','MillerFC','Campus Eleven','EagleFan','CollegeBall','UnitedOnTop','KeeperKing','MidfieldMaestro','StrikerFC'];const teams=['Blue Devils FC','Tar Heel United','Coastal XI','Campus Eleven F.C.','Eagles SC','Huskies United','Orange Pride','Demon Deacons','Spartan Squad','Wildcat XI'];return names.map((name,i)=>({rank:i+1,name,team:teams[i],total_points:Number((412.6-i*8.35).toFixed(1)),round_points:Number((78.4-i*1.25).toFixed(1)),you:i===3}))}
 const remote=rankingRemoteData(world,cat,conf);
 const snap=snapshotFor(world,cat);
 let data=[];
 if(cat==='standings')data=remote;
 else if(remote.length&&(world!=='D1'||!snap||remote.length>=(snap.items||[]).length))data=remote;
 else if(snap)data=snap.items.map(x=>({...x}));
 else if(['scorers','assists','clean_sheets','defenses'].includes(cat)){
   // Only verified local rows belong in statistical rankings. Prototype samples never become “official” leaderboards.
   const local=(world===state.activeWorld?state.players:[]).filter(x=>x.verified);
   if(cat==='scorers')data=local.filter(p=>p.goals>0).sort((a,b)=>b.goals-a.goals||(b.minutes||0)-(a.minutes||0));
   if(cat==='assists')data=local.filter(p=>p.assists>0).sort((a,b)=>b.assists-a.assists||(b.minutes||0)-(a.minutes||0));
   if(cat==='clean_sheets')data=local.filter(p=>(p.position==='GK'||p.position==='DF')&&p.shutouts>0).sort((a,b)=>b.shutouts-a.shutouts||(b.minutes||0)-(a.minutes||0));
   if(cat==='defenses')data=remote;
 }
 if(conf!=='all')data=data.filter(x=>x.conference===conf);
 return data;
}
function rankingMeta(world,cat){if(cat==='fantasy')return 'Fantasy manager leaderboard · prototype season';const snap=snapshotFor(world,cat);if(snap)return `Last updated: ${snap.updated} · ${snap.source}`;const remote=rankingRemoteData(world,cat,$('#standingConf')?.value||'all');const first=remote?.[0];if(first?.source_updated_text)return `${first.source_updated_text} · NCAA / United Soccer Coaches`;return cat==='national'?'NCAA / United Soccer Coaches only · live source when available':'Live/verified source data when available'}
function renderRankings(skipFetch=false){
 state.rankingWorld=$('#rankingWorld').value||state.rankingWorld;
 renderRankingConferenceOptions();
 const conf=$('#standingConf').value||'all';
 const cat=state.rankingCat;
 const data=rankData(state.rankingWorld,cat,conf);
 const titles={fantasy:'Fantasy Managers',scorers:'Top Scorers',assists:'Assist Leaders',clean_sheets:'Clean-sheet Leaders',national:'NCAA Rankings',standings:'Conference Standings',defenses:'Best Defenses'};
 $('#rankingTitle').textContent=titles[cat]||'Rankings';
 let subtitle='';
 if(cat==='fantasy')subtitle=`Top fantasy managers in ${worlds[state.rankingWorld].label}.`;
 else if(cat==='scorers')subtitle=`National verified goal leaders ${conf==='all'?'across all conferences':`in ${conf}`} in ${worlds[state.rankingWorld].label}.`;
 else if(cat==='assists')subtitle=`National verified assist leaders ${conf==='all'?'across all conferences':`in ${conf}`}.`;
 else if(cat==='clean_sheets')subtitle='Verified clean-sheet leaders. Zero entries are hidden.';
 else if(cat==='standings'&&conf==='all')subtitle=`All verified conference standings in ${worlds[state.rankingWorld].label}. Use the conference filter to narrow the table.`;
 else subtitle=`${worlds[state.rankingWorld].label}${conf==='all'?'':` · ${conf}`} · verified source data only.`;
 $('#rankingSubtitle').textContent=subtitle;
 $('#rankingUpdated').textContent=state.rankingSyncing?'Refreshing official data…':rankingMeta(state.rankingWorld,cat);
 renderRankingTable(data,cat,conf);renderQuickStats(data,cat);renderConferenceLeaders();save();
 if(!skipFetch&&cat!=='fantasy'){
   Promise.all([fetchRankingConferences(state.rankingWorld),fetchRankingRemote(state.rankingWorld,cat,conf)]).then(changed=>{
     if(changed.some(Boolean)){
       renderRankingConferenceOptions();
       renderRankings(true);
     }
   });
 }
}
function dash(v){return v===null||v===undefined||v===''?'—':v}
function renderRankingPager(total){
 const pager=$('#rankPager');if(!pager)return;
 const size=state.rankingPageSize||15;const pages=Math.max(1,Math.ceil(total/size));
 state.rankingPage=clamp(state.rankingPage||1,1,pages);
 if(total<=size){pager.innerHTML='';return;}
 let nums=[];for(let p=1;p<=pages;p++){if(p===1||p===pages||Math.abs(p-state.rankingPage)<=2)nums.push(p)}
 const unique=[...new Set(nums)];let html=`<button data-rank-page="${Math.max(1,state.rankingPage-1)}" ${state.rankingPage===1?'disabled':''}>‹</button>`;
 let last=0;for(const p of unique){if(last&&p-last>1)html+='<span class="pager-gap">…</span>';html+=`<button class="${p===state.rankingPage?'active':''}" data-rank-page="${p}">${p}</button>`;last=p}
 html+=`<button data-rank-page="${Math.min(pages,state.rankingPage+1)}" ${state.rankingPage===pages?'disabled':''}>›</button>`;pager.innerHTML=html;
 $$('[data-rank-page]').forEach(b=>b.onclick=()=>{state.rankingPage=Number(b.dataset.rankPage)||1;renderRankings(true)});
}
function renderRankingTable(data,cat,conf='all'){
 let head='',rows='';const size=state.rankingPageSize||15;const total=data.length;const pages=Math.max(1,Math.ceil(total/size));state.rankingPage=clamp(state.rankingPage||1,1,pages);const start=(state.rankingPage-1)*size;const pageData=data.slice(start,start+size);
 if(cat==='fantasy'){head=`<div class="rank-table-head fantasy-head"><span>#</span><span>Manager</span><span>Team</span><span>Total Pts</span><span>Round Pts</span><span></span></div>`;rows=pageData.map((m,i)=>`<div class="rank-row fantasy-row ${m.you?'you-row':''}"><span class="rank-num">${m.rank||start+i+1}</span><span class="rank-player"><b>${m.name}${m.you?' (You)':''}</b></span><span>${m.team}</span><span class="rank-value">${m.total_points}</span><span>${m.round_points}</span><span>${m.you?'★':''}</span></div>`).join('');$('#rankingTable').innerHTML=head+rows;$('#rankShowing').textContent=total?`Showing ${start+1}–${Math.min(start+size,total)} of ${total}`:'0 entries';renderRankingPager(total);return}
 if(['scorers','assists','clean_sheets'].includes(cat)){const key=cat==='scorers'?'goals':cat==='assists'?'assists':'shutouts';head=`<div class="rank-table-head"><span>#</span><span>Player</span><span>School</span><span>Conference</span><span>${key==='shutouts'?'Clean Sheets':key[0].toUpperCase()+key.slice(1)}</span><span>Minutes</span></div>`;rows=pageData.map((p,i)=>`<div class="rank-row"><span class="rank-num">${p.rank||start+i+1}</span><span class="rank-player"><b>${p.name}</b><span>${p.position||'—'}</span></span><span>${p.school||'—'}</span><span>${p.conference||'—'}</span><span class="rank-value">${dash(p[key])}</span><span>${dash(p.minutes==null?null:Math.round(p.minutes))}</span></div>`).join('')}
 else if(cat==='national'){head=`<div class="rank-table-head"><span>#</span><span>School</span><span>Conference</span><span>W-L-T</span><span>Points</span><span>Previous</span></div>`;rows=pageData.map((t,i)=>`<div class="rank-row"><span class="rank-num">${t.rank_label||t.rank||start+i+1}</span><span class="rank-player"><b>${t.school}</b></span><span>${t.conference||'—'}</span><span>${t.overall_record||t.record||'—'}</span><span class="rank-value">${dash(t.total_points??t.score)}</span><span>${dash(t.previous)}</span></div>`).join('')}
 else if(cat==='standings'){head=`<div class="rank-table-head"><span>#</span><span>School</span><span>Conference</span><span>Conf. W-L-T</span><span>Overall W-L-T</span><span>Source</span></div>`;rows=pageData.map((t,i)=>`<div class="rank-row"><span class="rank-num">${start+i+1}</span><span class="rank-player"><b>${t.school}</b></span><span>${t.conference||conf}</span><span>${t.conference_record||'—'}</span><span class="rank-value">${t.overall_record||'—'}</span><span>${t.source||'Verified source'}</span></div>`).join('')}
 else{head=`<div class="rank-table-head"><span>#</span><span>School</span><span>Conference</span><span>Games</span><span>Clean Sheets</span><span>GA</span></div>`;rows=pageData.map((t,i)=>`<div class="rank-row"><span class="rank-num">${start+i+1}</span><span class="rank-player"><b>${t.school}</b></span><span>${t.conference||'—'}</span><span>${dash(t.games)}</span><span class="rank-value">${dash(t.clean_sheets)}</span><span>${dash(t.goals_against)}</span></div>`).join('')}
 if(!rows)rows='<div class="ranking-empty"><b>No verified entries loaded yet</b><span>Press Refresh to import the available official ranking data. No standings or player leaders are fabricated.</span></div>';
 $('#rankingTable').innerHTML=head+rows;$('#rankShowing').textContent=total?`Showing ${start+1}–${Math.min(start+size,total)} of ${total}`:'0 verified entries';renderRankingPager(total)
}
function renderQuickStats(data,cat){let stats;if(cat==='scorers'){stats=[[data.length,'Players with goals'],[data.length?((data.reduce((s,p)=>s+Number(p.goals||0),0)/data.length).toFixed(1)):0,'Avg. goals per player'],[data.reduce((s,p)=>s+Number(p.goals||0),0),'Total goals'],[new Set(data.map(p=>p.school).filter(Boolean)).size,'Schools represented']]}else if(cat==='assists'){stats=[[data.length,'Players with assists'],[data.reduce((s,p)=>s+Number(p.assists||0),0),'Total assists'],[new Set(data.map(p=>p.school).filter(Boolean)).size,'Schools represented'],[new Set(data.map(p=>p.conference).filter(Boolean)).size,'Conferences']]}else{stats=[[data.length,'Verified entries'],[new Set(data.map(p=>p.school).filter(Boolean)).size,'Schools'],[new Set(data.map(p=>p.conference).filter(Boolean)).size,'Conferences'],[2026,'Season']]}$('#quickStats').innerHTML=stats.map(s=>`<div class="quick-stat"><b>${s[0]}</b><span>${s[1]}</span></div>`).join('')}
function renderConferenceLeaders(){const players=rankData(state.rankingWorld,'scorers','all');const agg={};players.filter(p=>Number(p.goals)>0&&p.conference).forEach(p=>agg[p.conference]=(agg[p.conference]||0)+Number(p.goals));$('#conferenceLeaders').innerHTML=Object.entries(agg).sort((a,b)=>b[1]-a[1]).slice(0,8).map(([c,v])=>`<div class="conf-leader"><span>${c}</span><b>${v}</b></div>`).join('')||'<div class="fine">No verified conference totals loaded.</div>'}

function toggleWorldParticipation(world){state.participation[world]=!state.participation[world];save();renderDashboard();renderCompetitions();toast(state.participation[world]?`${worlds[world].label}: joined.`:`${worlds[world].label}: left. Your saved lineup stays available if you rejoin.`)}
function renderCompetitions(){$('#myLeagues').innerHTML=state.leagues.map((l,i)=>`<article class="panel league-card"><div class="eyebrow">${worlds[l.world].label}</div><h3>${l.name}</h3><p>${l.members} managers · private fantasy league</p><div class="league-rank"><span>Your rank</span><b>#${l.rank}</b></div><div class="league-actions"><button class="leave-league-btn" data-leave-league="${i}">LEAVE LEAGUE</button></div></article>`).join('');$('#worldCards').innerHTML=worldOrder.map(w=>`<div class="world-card ${state.participation[w]?'active':''}"><div class="eyebrow">${worlds[w].label}</div><h3>${money(worlds[w].budget)}</h3><p>Independent budget, lineup, boosts, scoring and leagues.</p><button class="btn ${state.participation[w]?'btn-soft':'btn-primary'} btn-full" data-world-play="${w}">${state.participation[w]?'LEAVE WORLD':'JOIN WORLD'}</button></div>`).join('');$$('[data-world-play]').forEach(b=>b.onclick=()=>toggleWorldParticipation(b.dataset.worldPlay));$$('[data-leave-league]').forEach(b=>b.onclick=()=>{const i=Number(b.dataset.leaveLeague);const league=state.leagues[i];if(!league)return;state.leagues.splice(i,1);save();renderCompetitions();toast(`Left ${league.name}.`)})}

function buildGameFilterOptions(){
 const conf=$('#gamesConference'),school=$('#gamesSchool');if(!conf||!school)return;
 const gameConfs=state.games.flatMap(g=>[g.home_conference,g.away_conference]).filter(Boolean);const confs=[...new Set([...(state.teamRows||[]).map(t=>t.conference).filter(Boolean),...gameConfs])].sort();conf.innerHTML=optionHtml('all',tr('allConferences'))+confs.map(x=>optionHtml(x)).join('');conf.value=confs.includes(state.gameConference)?state.gameConference:'all';state.gameConference=conf.value;
 const schools=[];(state.teamRows||[]).filter(t=>state.gameConference==='all'||t.conference===state.gameConference).forEach(t=>t.school&&schools.push(t.school));state.games.forEach(g=>{if(state.gameConference==='all'||gameConference(g,'home')===state.gameConference)g.home_team&&schools.push(g.home_team);if(state.gameConference==='all'||gameConference(g,'away')===state.gameConference)g.away_team&&schools.push(g.away_team)});const unique=[...new Set(schools)].sort();school.innerHTML=optionHtml('all',tr('allSchools'))+unique.map(x=>optionHtml(x)).join('');school.value=unique.includes(state.gameSchool)?state.gameSchool:'all';state.gameSchool=school.value;
 const dateInput=$('#gamesDate');if(dateInput)dateInput.value=state.gameDate||isoToday();
}
function parseIsoLocal(iso){const [y,m,d]=String(iso).split('-').map(Number);return new Date(y,m-1,d,12,0,0)}
function isoFromDate(d){return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function dateLong(iso){try{return new Intl.DateTimeFormat(state.lang==='pt'?'pt-BR':state.lang==='es'?'es-ES':'en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'}).format(parseIsoLocal(iso))}catch(e){return iso}}
function renderDateStrip(){const wrap=$('#gamesDateStrip');if(!wrap)return;const center=parseIsoLocal(state.gameDate||isoToday());const days=[];for(let i=-3;i<=3;i++){const d=new Date(center);d.setDate(center.getDate()+i);const iso=isoFromDate(d);days.push(`<button class="date-chip ${iso===state.gameDate?'active':''}" data-game-date="${iso}"><small>${new Intl.DateTimeFormat(state.lang==='pt'?'pt-BR':state.lang==='es'?'es-ES':'en-US',{weekday:'short'}).format(d).replace('.','')}</small><b>${d.getDate()}</b></button>`)}wrap.innerHTML=days.join('');$$('[data-game-date]').forEach(b=>b.onclick=()=>setGameDate(b.dataset.gameDate))}
function setGameDate(date){
 state.gameDate=date||isoToday();save();
 // Date buttons are local-first: change the screen immediately, then read only
 // that date from SQLite. No automatic NCAA request and no seven-day prefetch.
 renderGames();
 const requested=state.gameDate;
 setTimeout(()=>syncSelectedGameDate(requested).then(()=>{if(state.gameDate===requested&&$('.page.active')?.id==='games')renderGames()}),0);
}

function gameStartMinutes(value){
 const text=String(value||'').trim();
 let m=text.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
 if(m){let h=Number(m[1])%12;if(String(m[3]).toUpperCase()==='PM')h+=12;return h*60+Number(m[2])}
 m=text.match(/^(\d{1,2}):(\d{2})$/);if(m)return Number(m[1])*60+Number(m[2]);
 return 9999;
}
function gameCardHtml(g){const live=isLive(g),final=isFinal(g),hasScore=g.home_score!=null&&g.away_score!=null,past=String(g.game_date||'')<isoToday();const status=live?(g.status||'LIVE'):(final||(hasScore&&past))?'FINAL':(g.start_time||'SCHEDULED');const h=g.home_score??'–',a=g.away_score??'–';const scoreVisible=live||final||hasScore;return`<article class="ncaa-game-card ${live?'live-game':''}"><div class="ncaa-game-top"><span class="game-time ${live?'live-text':''}">${status}</span>${g.source_url?`<a href="${g.source_url}" target="_blank" rel="noreferrer">NCAA ↗</a>`:''}</div><div class="ncaa-team-row"><span class="team-mark">${(g.away_team||'?').slice(0,2).toUpperCase()}</span><b>${g.away_team}</b><strong>${scoreVisible?a:' '}</strong></div><div class="ncaa-team-row"><span class="team-mark">${(g.home_team||'?').slice(0,2).toUpperCase()}</span><b>${g.home_team}</b><strong>${scoreVisible?h:' '}</strong></div></article>`}
function renderGames(){
 const worldTag=$('#gamesWorldEyebrow');if(worldTag)worldTag.textContent=`${worlds[state.activeWorld].label} · 2026`;if($('#gamesOfficialSource'))$('#gamesOfficialSource').href=worlds[state.activeWorld].source;
 buildGameFilterOptions();renderDateStrip();const f=state.gameFilter;const conf=state.gameConference||'all',school=state.gameSchool||'all',date=state.gameDate||isoToday();let data=state.games.filter(g=>g.game_date===date&&gameMatches(g,conf,school)&&(f==='all'||f==='live'&&isLive(g)||f==='scheduled'&&scheduled(g)||f==='finished'&&isFinal(g)));
 data.sort((a,b)=>{if(isLive(a)!==isLive(b))return isLive(a)?-1:1;return gameStartMinutes(a.start_time)-gameStartMinutes(b.start_time)||String(a.away_team).localeCompare(String(b.away_team))});
 const title=$('#gamesDateTitle');if(title)title.textContent=`${tr('gamesOn')} ${dateLong(date)}`;
 const coverage=$('#gamesCoverage');if(coverage){const total=state.gameCoverage?.games??state.games.length;const schools=state.gameCoverage?.schools_with_games??new Set(state.games.flatMap(g=>[g.home_team,g.away_team]).filter(Boolean)).size;coverage.innerHTML=`${data.length} games on this date · ${total} verified 2026 games stored · ${schools} schools represented${state.seasonSyncing[state.activeWorld]?' · <span class="sync-progress syncing">SYNCING FULL 2026 SEASON…</span>':''}`}
 $('#gamesList').innerHTML=data.map(gameCardHtml).join('')||'<div class="data-empty"><b>No games are cached for this date yet.</b><br>The official schedule is checked automatically when you select the date.</div>';
 $$('.game-tabs button').forEach(x=>x.classList.toggle('active',x.dataset.gameFilter===state.gameFilter));
}
async function syncSelectedGameDate(date){
 if(!date)return;
 const payload=await jfetch(query('/api/games-date',{division:state.activeWorld,date}),{items:[]});
 const items=Array.isArray(payload)?payload:(payload?.items||[]);
 if(Array.isArray(items)){replaceGameDate(date,items);if($('.page.active')?.id==='games')renderGames()}
}
async function refreshSelectedGameDate(date,wait=false){
 if(!date)return;
 try{
  // Exact-date upstream refreshes have short server-side fallbacks. Give the
  // server enough time to try NCAA API + direct NCAA without aborting early.
  const payload=await jfetch(query('/api/games-date',{division:state.activeWorld,date,refresh:1,wait:wait?1:0}),{items:[]},wait?14500:2500);
  const items=payload?.items||[];
  if(Array.isArray(items)){replaceGameDate(date,items);if($('.page.active')?.id==='games')renderGames();renderScores()}
  else if(!wait){setTimeout(()=>syncSelectedGameDate(date),1800)}
  else if($('.page.active')?.id==='games'){renderGames()}
 }catch(e){if(wait&&$('.page.active')?.id==='games')renderGames()}
}
async function prefetchGameStrip(centerIso){
 const center=parseIsoLocal(centerIso||isoToday());
 const offsets=[0,1,2,3,-1,-2,-3];
 const dates=offsets.map(i=>{const d=new Date(center);d.setDate(center.getDate()+i);return isoFromDate(d)});
 // Read every visible date from SQLite first. Future dates are deliberately
 // prioritized because managers are most likely to click forward in the schedule.
 const reads=dates.map(d=>jfetch(query('/api/games-date',{division:state.activeWorld,date:d}),{items:[]},1600).then(p=>({d,items:p?.items||[]})));
 const results=await Promise.all(reads);
 const missing=[];results.forEach(r=>{replaceGameDate(r.d,r.items);if(!r.items.length)missing.push(r.d)});
 if($('.page.active')?.id==='games')renderGames();renderScores();
 // Warm all missing dates shown in the seven-day strip. Each call refreshes one
 // date only; spacing keeps us comfortably below public-source rate limits.
 missing.forEach((d,i)=>setTimeout(()=>refreshSelectedGameDate(d,false),i*650));
}
async function syncGamesOnly(){
 const b=$('#gamesSync');if(b)b.disabled=true;
 const world=state.activeWorld,date=state.gameDate||isoToday();
 try{
  toast('Updating this date from the official schedule…');
  await refreshSelectedGameDate(date,true);
  await syncSelectedGameDate(date);
  prefetchGameStrip(date);
  // The season-wide job is useful for future instant navigation, but it must
  // never block the selected day or freeze the UI.
  fetch('/api/sync-games',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({division:world,start_date:'2026-08-01',end_date:'2026-12-31',background:true})}).catch(()=>{});
  toast('Selected date updated. Full 2026 cache is warming in the background.');
 }catch(e){toast('The official schedule could not be refreshed right now. Cached games were kept.')}finally{if(b)b.disabled=false;renderGames()}
}
async function refreshStatsCoverage(){const w=state.activeWorld;const cov=await jfetch(query('/api/player-stats-coverage',{division:w}),state.statsCoverage||{});if(state.activeWorld===w){state.statsCoverage=cov;if($('.page.active')?.id==='market')renderMarket()}return cov}
async function ensurePlayerStatsSync(force=false){const w=state.activeWorld;if(state.statsSyncing[w])return;const cov=await refreshStatsCoverage();const total=Number(cov?.players||state.players.length||0),done=Number(cov?.players_with_verified_stats||0);if(!force&&(total===0||done>=total*.95))return;state.statsSyncing[w]=true;try{const r=await fetch('/api/sync-player-stats',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({division:w})});const j=await r.json();if(j?.running){state.statsCoverage={...(state.statsCoverage||{}),running:true};if(force)toast('Full official player-stat sync started. You can keep using the site.');let polls=0;const timer=setInterval(async()=>{polls++;const c=await jfetch(query('/api/player-stats-coverage',{division:w}),{});if(state.activeWorld===w){state.statsCoverage=c;if($('.page.active')?.id==='market')renderMarket()}if(!c?.running||polls>=120){clearInterval(timer);state.statsSyncing[w]=false;if(state.activeWorld===w){const [ps,cs]=await Promise.all([jfetch(query('/api/players',{division:w}),[]),jfetch(query('/api/coaches',{division:w}),[])]);state.players=(ps||[]).map(normalizeApiPlayer);state.coaches=(cs||[]).map(c=>({...c,id:`API-C${c.id}`,rating:clamp(Math.round(70+((Number(c.price||5)-4)/6)*28),70,98),verified:Boolean(c.source_url),hasStats:true}));renderMarket()}}},10000)}}catch(e){state.statsSyncing[w]=false}}

async function syncNow(){ensurePlayerStatsSync(true);const buttons=[$('#marketSync'),$('#refreshNews')].filter(Boolean);buttons.forEach(b=>b.disabled=true);try{const r=await fetch('/api/sync',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({division:state.activeWorld})});if(!r.ok)throw new Error();toast('Verified public-source sync completed where available.');await loadWorld(state.activeWorld)}catch(e){toast('Live sync was unavailable. Existing verified data was kept.')}finally{buttons.forEach(b=>b.disabled=false)}}
function openProfile(){openModal(`<div class="eyebrow">PROFILE</div><h2>${state.profile.team}</h2><p>@${state.profile.handle} · 2026 season</p><div class="profile-edit-grid"><label>Team name<input id="profileTeamInput" value="${state.profile.team}"></label><label>Manager handle<input id="profileHandleInput" value="${state.profile.handle}"></label></div><button id="saveProfileBtn" class="btn btn-primary btn-full" style="margin-top:12px">SAVE PROFILE</button><button id="logoutBtn" class="btn btn-soft btn-full" style="margin-top:8px">LOG OUT</button>`);setTimeout(()=>{const saveBtn=$('#saveProfileBtn');if(saveBtn)saveBtn.onclick=()=>{state.profile.team=$('#profileTeamInput').value.trim()||'Campus Eleven F.C.';state.profile.handle=$('#profileHandleInput').value.trim().replace(/^@/,'')||'manager';state.profile.initials=(state.profile.handle.slice(0,2)||'LC').toUpperCase();save();renderWorldSelectors();closeModal();toast('Profile updated.')};$('#logoutBtn').onclick=()=>{sessionStorage.removeItem('college_fantasy_v1_authenticated');closeModal();$('#appShell').classList.add('hidden');$('#loginScreen').classList.remove('hidden')}} ,0)}
function showNotifications(){openModal(`<div class="eyebrow">NOTIFICATIONS</div><h2>Manager Center</h2><div class="notification-list"><div class="notification-item"><b>⚽ Market is open</b><span>Review your lineup before Saturday at 2:59 PM ET.</span></div><div class="notification-item"><b>📅 Games & Results</b><span>Today’s live games and the next scheduled matches are available from the dashboard.</span></div><div class="notification-item"><b>🏆 Rankings</b><span>Use Refresh when you want to request the latest official public-source snapshot.</span></div></div><button id="notifLineup" class="btn btn-primary btn-full">OPEN LINEUP</button>`);setTimeout(()=>{$('#notifLineup').onclick=()=>{closeModal();show('team')}},0)}
function showScoring(){openModal(`<div class="eyebrow">FANTASY SCORING</div><h2>${tr('howScoring')}</h2><p>Players score from real match events with position-specific logic for goals, assists, minutes, clean sheets, cards, saves and team results. Head Coach and Assistant Coach scoring is tied to team performance. Associate Head Coaches are eligible in the Assistant Coach slot.</p>`)}
async function refreshRankingData(){
 const b=$('#rankingRefresh');if(state.rankingSyncing)return;state.rankingSyncing=true;if(b)b.disabled=true;renderRankings(true);toast('Refreshing official rankings and player leaders…');
 try{
   const r=await fetch('/api/sync-rankings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({division:state.rankingWorld})});
   const payload=await r.json();if(!r.ok||!payload.ok)throw new Error(payload.error||'Ranking refresh unavailable');
   Object.keys(state.rankingRemote).filter(k=>k.startsWith(state.rankingWorld+'|')).forEach(k=>delete state.rankingRemote[k]);delete state.rankingConferences[state.rankingWorld];
   await fetchRankingConferences(state.rankingWorld,true);
   const conf=$('#standingConf')?.value||'all';
   await fetchRankingRemote(state.rankingWorld,state.rankingCat,conf,true);
   renderRankingConferenceOptions();$('#standingConf').value=rankingBaseConferences(state.rankingWorld).includes(conf)?conf:'all';state.rankingPage=1;toast('Rankings updated from verified public sources.');
 }catch(e){toast('Official ranking refresh was unavailable. Existing verified data was kept.')}finally{state.rankingSyncing=false;if(b)b.disabled=false;renderRankings(true)}
}

function bind(){
 document.addEventListener('click',e=>{const j=e.target.closest('[data-jump]');if(j){show(j.dataset.jump)}});
 $$('[data-lang]').forEach(b=>b.onclick=()=>{state.lang=b.dataset.lang;save();applyLang();renderAll()});$$('[data-login-lang]').forEach(b=>{b.type='button';b.onclick=()=>{state.lang=b.dataset.loginLang;save();applyLang()}});
 const doLogin=e=>{if(e)e.preventDefault();const email=$('#loginEmail').value.trim(),pass=$('#loginPassword').value;if(!email||!pass){toast('Enter an email and password.');return}sessionStorage.setItem('college_fantasy_v1_authenticated','1');$('#loginScreen').classList.add('hidden');$('#appShell').classList.remove('hidden');boot(false);loadWorld(state.activeWorld)};
 $('#loginForm')?.addEventListener('submit',doLogin);if($('#enterApp'))$('#enterApp').type='submit';
 if($('#togglePassword'))$('#togglePassword').onclick=()=>{const i=$('#loginPassword');const show=i.type==='password';i.type=show?'text':'password';$('#togglePassword').textContent=show?'Hide':'Show'};
 if($('#demoLogin'))$('#demoLogin').onclick=()=>doLogin();
 if($('#forgotPassword'))$('#forgotPassword').onclick=()=>openModal(`<div class="eyebrow">ACCOUNT ACCESS</div><h2>Reset password</h2><p>Enter your email. In the production handoff this connects to the authentication provider.</p><input id="resetEmail" class="modal-input" type="email" value="${$('#loginEmail')?.value||''}" placeholder="Email"><button id="sendResetBtn" class="btn btn-primary btn-full">SEND RESET LINK</button>`);
 if($('#createAccountLogin'))$('#createAccountLogin').onclick=()=>openModal(`<div class="eyebrow">NEW MANAGER</div><h2>Create your fantasy profile</h2><div class="profile-edit-grid"><label>Team name<input id="signupTeam" value="Campus Eleven F.C."></label><label>Manager handle<input id="signupHandle" value="manager"></label></div><input id="signupEmail" class="modal-input" type="email" placeholder="Email"><input id="signupPassword" class="modal-input" type="password" placeholder="Password"><button id="signupBtn" class="btn btn-primary btn-full">CREATE & ENTER</button>`);
// The header division selector is GLOBAL: it works from Dashboard, Lineup,
 // Market, Rankings, Competitions and Games & Results without forcing a page change.
 // Keep the currently visible page on screen while the selected division hydrates.
 document.addEventListener('change',e=>{
  const el=e.target;
  if(!el||el.id!=='worldSelector')return;
  const next=el.value;
  if(!worldOrder.includes(next)||next===state.activeWorld)return;
  const currentPage=$('.page.active')?.id||'dashboard';
  // Rankings has its own world state; keep it aligned with the global selector.
  if(currentPage==='rankings')state.rankingWorld=next;
  // Market also has a local division select; mirror the header immediately.
  const marketDivision=$('#filterDivision');
  if(marketDivision)marketDivision.value=next;
  // Switch the active world without navigating away from the current page.
  // loadWorld() paints cached/local content first and keeps the page active.
  void loadWorld(next).then(()=>{
   if($('.page.active')?.id!==currentPage)return;
   if(currentPage==='rankings'){
    state.rankingWorld=next;
    renderRankingConferenceOptions();
    renderRankings();
   }else if(currentPage==='market'){
    refreshMarketDependentFilters();
    renderMarket();
   }else if(currentPage==='team'){
    renderTeam();
   }else if(currentPage==='games'){
    renderGames();
   }else if(currentPage==='competitions'){
    renderCompetitions();
   }else if(currentPage==='daily-games'){
    renderDailyGames();
   }else if(currentPage==='daily-pickem'){
    state.dailyPickemCache={};state.dailyPickemDate=isoToday();state.dailyPickemMode='today';renderDailyPickem();loadDailyPickemForDate(state.dailyPickemDate);
   }else if(currentPage==='daily-guess'){
    state.dailyGuessRuntime=null;state.dailyGuessSelected=null;renderDailyGuess();loadDailyGuess();
   }else{
    renderDashboard();
   }
  });
 });
 if($('#filterDivision'))$('#filterDivision').onchange=e=>{state.marketVisibleCount=60;['filterPos','filterConf','filterSchool','filterClass'].forEach(id=>{const el=$('#'+id);if(el)el.value='all'});show('market');loadWorld(e.target.value).then(()=>{refreshMarketDependentFilters();if($('.page.active')?.id==='market')renderMarket()})};
 if($('#filterEntity'))$('#filterEntity').onchange=()=>{state.marketVisibleCount=60;$('#filterPos').value='all';$('#filterClass').value='all';state.marketContext={type:$('#filterEntity').value,position:'all',bench:false};refreshMarketDependentFilters('entity');renderMarket();setTimeout(()=>ensureMarketData($('#filterEntity').value,'all'),0)};if($('#filterPos'))$('#filterPos').onchange=()=>{state.marketVisibleCount=60;state.marketContext.position=$('#filterPos').value;refreshMarketDependentFilters('position');renderMarket();if(($('#filterEntity')?.value||'players')==='players')setTimeout(()=>ensureMarketData('players',$('#filterPos').value),0)};if($('#filterClass'))$('#filterClass').onchange=()=>{state.marketVisibleCount=60;refreshMarketDependentFilters('class');renderMarket()};if($('#filterConf'))$('#filterConf').onchange=()=>{state.marketVisibleCount=60;refreshMarketDependentFilters('conf');renderMarket()};if($('#filterSchool'))$('#filterSchool').onchange=()=>{state.marketVisibleCount=60;refreshMarketDependentFilters('school');renderMarket()};if($('#filterSort'))$('#filterSort').onchange=()=>{state.marketVisibleCount=60;renderMarket()};if($('#filterSearch'))$('#filterSearch').oninput=()=>{state.marketVisibleCount=60;renderMarket()};
 if($('#clearFilters'))$('#clearFilters').onclick=()=>{state.marketVisibleCount=60;$('#filterEntity').value='players';$('#filterPos').value=state.marketContext?.position||'all';$('#filterConf').value='all';$('#filterSchool').value='all';$('#filterClass').value='all';$('#filterSort').value='rating_desc';$('#filterSearch').value='';refreshMarketDependentFilters();renderMarket()};if($('#howScoring'))$('#howScoring').onclick=showScoring;if($('#confirmTeam'))$('#confirmTeam').onclick=()=>toast($('#confirmTeam').disabled?'Complete 11 starters + Head Coach + Assistant Coach first.':'Lineup confirmed for this world.');if($('#stadiumViewBtn'))$('#stadiumViewBtn').onclick=()=>toast('College field view is active.');if($('#openAnyMarket'))$('#openAnyMarket').onclick=()=>openMarketFor('players','all',false);if($('#backToLineup'))$('#backToLineup').onclick=()=>show('team');
 if($('#browsePredictions'))$('#browsePredictions').onclick=()=>{state.dailyPickemMode='today';state.dailyPickemDate=isoToday();show('daily-pickem')};if($('#savePreviewPredictions'))$('#savePreviewPredictions').onclick=savePreview;if($('#viewAllResults'))$('#viewAllResults').onclick=()=>{state.gameFilter='all';state.gameDate=isoToday();show('games');setGameDate(state.gameDate)};if($('#seeAllScores'))$('#seeAllScores').onclick=()=>{state.gameDate=isoToday();show('games');setGameDate(state.gameDate)};if($('#gamesThisRound'))$('#gamesThisRound').onclick=()=>{state.gameDate=isoToday();show('games');setGameDate(state.gameDate)};if($('#lineupReminder'))$('#lineupReminder').onclick=()=>{const on=sessionStorage.getItem('college_fantasy_v1_lineup_reminder')==='1';sessionStorage.setItem('college_fantasy_v1_lineup_reminder',on?'0':'1');$('#lineupReminder').textContent=on?'🔔 LINEUP REMINDER':'✓ REMINDER SET';toast(on?'Lineup reminder removed.':'Lineup reminder set for this session.');};if($('#marketSync'))$('#marketSync').onclick=syncNow;if($('#refreshNews'))$('#refreshNews').onclick=()=>refreshNewsLive(true,true);if($('#quickCreateLeague'))$('#quickCreateLeague').onclick=()=>show('competitions');
 $$('.news-tabs [data-news-filter]').forEach(b=>b.onclick=()=>{$$('.news-tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active');state.newsFilter=b.dataset.newsFilter;renderNews()});$$('.ranking-tabs [data-ranking-cat]').forEach(b=>b.onclick=()=>{state.rankingCat=b.dataset.rankingCat;state.rankingPage=1;$$('.ranking-tabs button').forEach(x=>x.classList.toggle('active',x===b));renderRankings()});$$('[data-ranking-cat-jump]').forEach(b=>b.onclick=()=>{state.rankingCat=b.dataset.rankingCatJump;state.rankingPage=1;$$('.ranking-tabs button').forEach(x=>x.classList.toggle('active',x.dataset.rankingCat===state.rankingCat));renderRankings()});
 if($('#rankingWorld'))$('#rankingWorld').onchange=e=>{state.rankingWorld=e.target.value;state.rankingPage=1;delete state.rankingConferences[state.rankingWorld];renderRankingConferenceOptions();renderRankings()};if($('#standingConf'))$('#standingConf').onchange=()=>{state.rankingPage=1;renderRankings()};if($('#rankingRefresh'))$('#rankingRefresh').onclick=refreshRankingData;$$('.game-tabs button[data-game-filter]').forEach(b=>b.onclick=()=>{state.gameFilter=b.dataset.gameFilter;renderGames()});if($('#openPickemFromGames'))$('#openPickemFromGames').onclick=()=>{state.dailyPickemMode='today';state.dailyPickemDate=state.gameDate||isoToday();show('daily-pickem')};
 if($('#gamesConference'))$('#gamesConference').onchange=e=>{state.gameConference=e.target.value;state.gameSchool='all';renderGames()};if($('#gamesSchool'))$('#gamesSchool').onchange=e=>{state.gameSchool=e.target.value;const meta=(state.teamRows||[]).find(t=>t.school===state.gameSchool);if(meta?.conference){state.gameConference=meta.conference}renderGames()};if($('#gamesDate'))$('#gamesDate').onchange=e=>setGameDate(e.target.value);if($('#gamesCalendarBtn'))$('#gamesCalendarBtn').onclick=()=>{const el=$('#gamesDate');if(el.showPicker)el.showPicker();else el.focus()};if($('#gamesSync'))$('#gamesSync').onclick=syncGamesOnly;
 if($('#createLeague'))$('#createLeague').onclick=()=>openModal(`<div class="eyebrow">CREATE LEAGUE</div><h2>Create a fantasy league</h2><label>League name<input id="leagueName" class="modal-input" value="New College Soccer Fantasy League"></label><button id="createLeagueSave" class="btn btn-primary btn-full">CREATE</button>`);if($('#joinLeague'))$('#joinLeague').onclick=()=>openModal(`<div class="eyebrow">JOIN LEAGUE</div><h2>Join with a code</h2><input id="leagueCode" class="modal-input" placeholder="League code"><button id="joinLeagueSave" class="btn btn-primary btn-full">JOIN</button>`);document.addEventListener('click',e=>{if(e.target.id==='sendResetBtn'){toast('Reset-link flow is ready for authentication provider integration.');closeModal()}if(e.target.id==='signupBtn'){const team=$('#signupTeam')?.value.trim(),handle=$('#signupHandle')?.value.trim();if(team)state.profile.team=team;if(handle)state.profile.handle=handle.replace(/^@/,'');state.profile.initials=(state.profile.handle.slice(0,2)||'LC').toUpperCase();save();sessionStorage.setItem('college_fantasy_v1_authenticated','1');closeModal();$('#loginScreen').classList.add('hidden');$('#appShell').classList.remove('hidden');boot(false);loadWorld(state.activeWorld);}if(e.target.id==='createLeagueSave'){state.leagues.push({name:$('#leagueName').value||'New League',world:state.activeWorld,members:1,rank:1});save();closeModal();renderCompetitions();toast('League created.')}if(e.target.id==='joinLeagueSave'){state.leagues.push({name:'Joined League',world:state.activeWorld,members:16,rank:16});save();closeModal();renderCompetitions();toast('League joined.')}});$$('[data-action]').forEach(b=>b.onclick=()=>{if(['gamesPredictions','pickem'].includes(b.dataset.action)){state.dailyPickemMode='today';state.dailyPickemDate=isoToday();show('daily-pickem')} else if(b.dataset.action==='profile')openProfile();else if(b.dataset.action==='notifications')showNotifications();else toast('No new notifications.')});if($('#menuBtn'))$('#menuBtn').onclick=()=>$('#nav').classList.toggle('nav-open');if($('#modalClose'))$('#modalClose').onclick=closeModal;if($('#modal'))$('#modal').onclick=e=>{if(e.target.id==='modal')closeModal()};
}
function init(){applyLang();renderWorldSelectors();bind();renderBoost();const auth=sessionStorage.getItem('college_fantasy_v1_authenticated');if(auth){$('#loginScreen').classList.add('hidden');$('#appShell').classList.remove('hidden');boot(false);loadWorld(state.activeWorld)}else{$('#loginScreen').classList.remove('hidden');$('#appShell').classList.add('hidden');boot(false)}state.refreshTimersStarted=true}
init();
