// Build the editable teaching deck from saved report assets and statistics.
// Set MEDIDRONE_NODE_MODULES and MEDIDRONE_PRESENTATIONS_SKILL for a Codex bundled runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const modules=process.env.MEDIDRONE_NODE_MODULES;
if(modules)process.env.RUNTIME_NODE_MODULES ??= modules;
const ref=modules?pathToFileURL(path.join(modules,'@oai/artifact-tool/dist/artifact_tool.mjs')).href:'@oai/artifact-tool';
const {Presentation,PresentationFile}=await import(ref);
const skill=process.env.MEDIDRONE_PRESENTATIONS_SKILL;
if(!skill)throw Error('Set MEDIDRONE_PRESENTATIONS_SKILL to the installed presentations skill directory.');
const {resolvePresentationFont,finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const font=resolvePresentationFont();
const build=path.join(ROOT,'tmp/slides-build'); await fs.mkdir(build,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
const ink='#14283E', muted='#4B5B69', blue='#2563A6', orange='#C45A28';
const notes=[]; const tableOwners=[];
function text(s,t,x,y,w,h,size=30,color=ink,bold=false){
 const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=t;a.text.style={fontSize:size,typeface:font,color,bold};return a;
}
function slide(title,note,source='report/main.pdf'){
 const s=p.slides.add();s.background.fill='#FFFFFF';
 text(s,title,64,40,1150,85,42,ink,true);
 text(s,'CMP3005  /  MediDrone Istanbul',64,678,700,24,17,muted);
 text(s,String(p.slides.items.length).padStart(2,'0'),1160,678,60,24,17,muted);
 s.speakerNotes.text=note+'\n\nSource: '+source;
 notes.push({slide:p.slides.items.length,title,notes:note,source});return s;
}
function body(s,lines,y=155,size=30){lines.forEach((t,i)=>text(s,t,70,y+i*87,1130,74,size));}
function takeaway(s,t){text(s,t,70,605,1130,58,27,blue,true);}
function table(s,values,y=160,height=390,widths=null,size=24){
 const tb=s.tables.add({rows:values.length,columns:values[0].length,left:70,top:y,width:1140,height,values,...(widths?{columnWidths:widths}:{})});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=tb.getCell(r,c);cell.fill=r===0?ink:(r%2?'#F1F5F8':'#FFFFFF');
  cell.text.style={fontSize:size,typeface:font,color:r===0?'#FFFFFF':ink,bold:r===0};
 }
 tb.borders.assign({fill:'#D8E0E7',width:.6,style:'solid'});
 tableOwners.push(p.slides.items.length);return tb;
}
async function fig(s,name,x=90,y=145,w=1100,h=420){
 const bytes=await fs.readFile(path.join(ROOT,'figures/coursework',name+'.png'));
 s.images.add({blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),contentType:'image/png',alt:'Report figure: '+name,position:{left:x,top:y,width:w,height:h},fit:'contain'});
}
const summary=JSON.parse(await fs.readFile(path.join(ROOT,'results/summary.json'),'utf8'));
const main=summary.main;const num=(x,d=1)=>Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
let s=slide('MediDrone Istanbul','Açılış: Hangi drone hangi klinikleri hangi sırayla ziyaret etsin? Sunumda problemi küçük örnekle açıklayıp yöntemleri ve kayıtlı sonuçları karşılaştıracağım. Yaklaşık 12–15 dakika.');
text(s,'Medical delivery with limited payload',70,185,1100,70,44,blue,true);
text(s,'Genetic Algorithm and Tabu Search',70,280,1100,65,36);
text(s,'Faruk Alpay  ·  2267273\nCMP3005 Analysis of Algorithms\nFall 2026–2027',70,405,1100,140,28,muted);
s=slide('The delivery problem','Depo merkezde. Kesikli çizgi sentetik Boğaz sınırı. Her klinik bir kez ziyaret edilmeli, drone kapasitesi ve toplam drone sayısı aşılmamalı. Bu harita gerçek İstanbul koordinatları değil. Renk talebi gösteriyor. Seed 7273 öğrenci numaramın son dört hanesi.','report/main.pdf, Sections 1 and 4; figures/coursework/instance.png');
await fig(s,'instance',400,145,800,420);
text(s,'100 clinics\nCapacity Q = 100\nFleet K = 18\nCrossing P = 150',65,185,340,290,31);
takeaway(s,'Choose the clinic assignments and the visit order.');
s=slide('Why exact optimization is hard','NP üyeliği: rota listesini doğrulamak kolay. İndirgeme yönü zor problemden CVRP’ye. Birinci dönüşümde var olan kenarlar 1, olmayanlar 2 ve eşik N. İkinci dönüşümde tek drone K=1, kapasite n, her talep 1. Bin Packing için örnek 6,6,6 talep, iki adet 10 kapasiteli drone: toplam kapasite yeterli görünse de sığmaz.');
body(s,['A proposed plan can be checked in O(n) time.','Hamiltonian Cycle reduces to TSP, then to CVRP.','With K = 1, Q = n and unit demands, CVRP becomes TSP.','Even assigning loads to vehicles contains Bin Packing.']);
takeaway(s,'Easy to check does not mean easy to find.');
s=slide('Clarke–Wright savings','Başlangıçta her klinik ayrı rota. A ve B’yi birleştirdiğimde depoya giden iki bağlantının yerine A–B geliyor. Tasarruf 17. Yük uygunsa ve uygun rota uçlarıysa birleştiriyoruz. Yöntem her rota için kapasiteyi korur fakat toplam filo sınırını garanti etmez.','report/main.pdf, Section 5; Clarke & Wright (1964)');
table(s,[['Quantity','Cost'],['Depot to A','10'],['Depot to B','12'],['A to B','5'],['Saving: 10 + 12 − 5','17']],160,330,[800,340],29);
text(s,'Try the largest savings first; merge only if capacity allows.',70,525,1140,65,29);
takeaway(s,'A fast starting plan can still use too many drones.');
s=slide('Genetic Algorithm','Kromozom klinik sırası; rota ayırıcı yok. Tournament ile ebeveynler seçiliyor. OX her kliniğin bir kez kalmasını sağlıyor. Mutasyon sıra üzerinde değişiklik yapıyor. Split rotalara ayırıyor. Kopyaları elemek ve kısmi restart çeşitliliğe yardımcı. En iyi geçerli sonuç ayrı tutuluyor.','report/main.pdf, Sections 5–6; solver/src/ga.cpp');
body(s,['Chromosome: [3, 1, 4, 2] is a visit order.','Select parents, combine orders, then mutate the child.','Split chooses where one drone ends and the next begins.','Keep the best feasible answer; reject duplicates and restart.']);
takeaway(s,'The pure GA explores many orders without route-level local search.');
s=slide('Split DP with three clinics','Bu örnek rapordakiyle aynı. Depo 0, klinikler doğru üzerinde 1,2,3. Talepler 4,3,4, kapasite 7. Birinci kesme 10, ikinci kesme 8. D[j] ilk j kliniği servis etmenin en ucuz maliyeti. Son rotanın olası başlangıçlarını deniyoruz. Temel DP O(n²), rota uzunluğu L sınırlıysa O(nL). Koddaki hızlı kuyruk sürümü aynı kesme problemini hızlandırıyor.');
text(s,'Order [1, 2, 3]  ·  Demands [4, 3, 4]  ·  Capacity 7',70,145,1140,60,30);
table(s,[['Cut','Route costs','Total'],['[1, 2] / [3]','4 + 6','10'],['[1] / [2, 3]','2 + 6','8'],['[1, 2, 3]','Load 11 > 7','Invalid']],235,275,[510,360,270],28);
text(s,'D[j] = minimum of (best prefix cost + last route cost)',70,540,1140,55,29);
takeaway(s,'Split finds the best cuts for a fixed order, not the global optimum.');
s=slide('Tabu Search','TS tek rota planını değiştiriyor. Dört hamle relocate swap 2opt 2optstar. Silinen kenarlar 10–25 adım tabu oluyor. Yeni en iyi geçerli çözüm bulunacaksa aspiration yasağı kaldırıyor. Geçici aşırı yük cezayla mümkün, son kayıt mutlaka geçerli. Delta altı kenar terimi kullandığı için O(1); hamleyi uygulamak ayrıca maliyetli olabilir.','report/main.pdf, Section 7; solver/src/tabu.cpp');
body(s,['Move a clinic, swap two clinics or reconnect route segments.','Removed edges stay tabu for 10–25 iterations.','Aspiration allows a tabu move that creates a new best answer.','Temporary overload is penalized; the saved answer must be feasible.']);
takeaway(s,'Delta evaluation checks only changed edges in O(1).');
s=slide('A fair comparison','Bu tabloyu sonuçlardan önce anlat. Her yöntemin aynı örnekte aynı zamanı var. 1–10 değerlendirme seedleri, 101–105 tuning için ayrı. CW deterministik bir kez. Küçük örneklerde exact sonuç önceden hesaplandı, bu sunum için tekrar deney yok. Runtime ile en iyi cevabın bulunduğu zamanı karıştırma.','report/main.pdf, Section 4; experiments/common.py');
table(s,[['Setting','Protocol'],['Evaluation','10 recorded seeds per stochastic method'],['Small benchmarks','30 s for both GA and TS'],['Larger / team cases','60 s for both GA and TS'],['Tiny instances','1 s, compared with cached exact optima'],['Tuning','Separate seeds 101–105, 10 s per run']],155,350,[380,760],26);
text(s,'GA: population 100, crossover 0.9, mutation 1.0\nTS: 20 nearby candidates, tabu tenure 10–25',70,540,1140,85,27);
s=slide('Benchmark results','Maliyetler küçük olduğunda daha iyi. Ortalama tek şanslı koşudan daha anlamlı. SD farklı seedler arasındaki dağılım. TS ilk üç örnekte her koşuda BKS’ye ulaşıyor, son örnekte 6/10. Saf GA ortalama olarak geride. Bu sonuç bütün GA ve TS türleri için evrensel üstünlük kanıtı değil.','report/main.pdf, Section 9; results/coursework/main.csv');
const vr=[['Instance','Method','Mean cost','SD','Mean gap']];
for(const name of ['A-n32-k5','A-n45-k6','A-n60-k9','A-n80-k10'])for(const alg of ['ga','ts']){const r=main[name+'|'+alg];vr.push([name,alg.toUpperCase(),num(r.mean),num(r.std,2),num(r.gap_mean,2)+'%']);}
table(s,vr,150,410,[340,180,230,170,220],24);
takeaway(s,'TS has the lower mean cost on all four required benchmarks.');
s=slide('Results on the 100-clinic team instance','Burada referans kanıtlanmış optimum değil kayıtlı en iyi değer 20724.21095. CW 19 rota kullanıyor K18 olduğu için geçersiz, gap vermiyoruz. TS ortalama 20725.5 ve 9/10 koşuda referans. GA ortalama 21352.2. Ucuz görünen ama kısıtları bozan cevabı başarı saymıyoruz.','report/main.pdf, Sections 9–10; results/coursework/main.csv');
table(s,[['Method','Mean cost','SD','Mean gap'],['CW','22,573.3*','—','Infeasible'],['GA',num(main['MediDrone-7273|ga'].mean),num(main['MediDrone-7273|ga'].std,2),'3.03%'],['TS',num(main['MediDrone-7273|ts'].mean),num(main['MediDrone-7273|ts'].std,2),'0.006%']],165,260,[240,340,240,320],30);
text(s,'*CW uses 19 routes, but K = 18.\nReference = 20,724.21095 (best found, not a proven optimum).',70,470,1140,105,28);
takeaway(s,'Feasibility comes before comparing objective values.');
s=slide('Tiny cases with known exact answers','Dokuz örneğin her birinde 10 koşu var. GA için 90, TS için 90 başarılı koşu. DP ve MILP kayıtlı optimumları uyuşuyor. Bu küçük boyutta doğrulama sağlar, büyük problemlerin optimum çözüldüğünü kanıtlamaz.','report/main.pdf, Section 9; results/coursework/tiny.csv');
table(s,[['Instance','Exact cost','GA hits','TS hits'],...summary.tiny.map(r=>[r.name,num(r.opt,2),'10 / 10','10 / 10'])],145,420,[360,300,240,240],24);
takeaway(s,'Each method reaches the optimum in all 90 tiny runs.');
s=slide('How quickly do the methods improve?','Grafik A-n45-k6 için. Yatay eksen logaritmik zaman. Çizgi10koşunun medyanı, gölge ortadaki yüzde50. Kayıtlı en iyi cevap azaldıkça çizgi düşüyor. TS erken iyi cevap buluyor. Arama sırasında mevcut çözüm kötüleşebilir ama best-so-far asla artmaz.','report/main.pdf, Section 10; figures/coursework/convergence.png');
await fig(s,'convergence',90,140,1100,420);takeaway(s,'TS finds a strong answer early; GA improves more gradually.');
s=slide('The final team delivery plan','Renkler farklı drone rotaları. Plan 17 drone kullanıyor. 10 rota Avrupa’ya gidip geliyor: toplam 20 geçiş. Avrupa talebi 938, her drone 100 taşıyor, en az 10 drone gerekiyor. Bu plan geçiş sayısında alt sınıra ulaşıyor, toplam mesafe optimumluğu ayrı bir konu.','report/main.pdf, Section 10; figures/coursework/routes.png');
await fig(s,'routes',65,145,800,420);
text(s,'17 drones used\n10 crossing routes\n20 crossing edges\n20 × 150 = 3,000\npenalty cost units',890,180,320,310,30);
takeaway(s,'938 / 100 requires at least 10 drones to serve Europe.');
s=slide('Complexity checked against measurements','Sol grafik log-log. Sabit20aday TS lineer bekleniyor eğim1.08; bütün adaylar kuadratik eğim2.12. GA50popülasyonda0.84; sabit giderler küçük boyutta etkili. Sağda delta bütün çözümü tekrar toplamaktan çok ucuz. Ölçülen eğim ispat değil teorik analize destek.3200 noktasındaki TS sıçraması cache ve bellek etkisiyle uyumlu, kesin sebep iddiası yok.','report/main.pdf, Section 8; figures/coursework/complexity.png');
await fig(s,'complexity',65,140,1150,365);
text(s,'Fixed candidate list: O(nk), slope 1.08\nFull candidate list: O(n²), slope 2.12',70,530,1140,90,29);
s=slide('Parameter choice and crossing penalties','Solda çok kısa tabu hemen geri dönmeye izin veriyor, çok uzun tabu yararlı hareketi kısıtlıyor.10–25 iyi bir orta bölge. Sağda P 0’dan 1000’e artsa da 10 geçiş rotası değişmiyor. Rotalar zaten kapasitenin zorunlu minimumuna ulaştığı için ceza artırmak yapıyı değiştirmiyor. Olmamış etkiyi olmuş gibi anlatmıyoruz.','report/main.pdf, Section 11; figures/coursework/sensitivity.png');
await fig(s,'sensitivity',65,140,1150,365);
text(s,'Moderate tenure works well here.\nIncreasing P does not reorganize the best saved synthetic routes.',70,535,1140,85,29);
s=slide('What the results support','Sonuçları sınırlarıyla özetle. TS bu implementasyonlarda daha iyi ortalama. Küçük örnekler ve bağımsız checker doğrulamaya yardımcı. Model sentetik koordinatlar ve yük kapasitesi kullanıyor. Batarya, rüzgar, uçuş izinleri ve zaman pencereleri yok. Gelecekte GA’ya local search eklemek mantıklı, mevcut MA kodu var. Sorularda Split örneğine veya TS delta formülüne geri dön.','report/main.pdf, Sections 11–12');
body(s,['TS gives lower mean costs in this controlled comparison.','Exact tiny cases and an independent checker support correctness.','The model includes capacity and crossings, but omits battery and time windows.','A next step is a controlled GA comparison with local search.'],155,30);
takeaway(s,'Good measured performance is evidence, not a universal guarantee.');
await fs.writeFile(path.join(ROOT,'slides/speaker_notes_TR.md'),notes.map(n=>`## ${n.slide}. ${n.title}\n\n${n.notes}\n\nKaynak: ${n.source}\n`).join('\n'));
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
for(let i=0;i<p.slides.items.length;i++){
 const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const outputDir=path.join(ROOT,'tmp/slides-output');await fs.mkdir(outputDir,{recursive:true});
const final=path.join(outputDir,`validated-${Date.now()}.pptx`);
const destination=path.join(ROOT,'deliverables/CMP3005_Slides_FarukAlpay_2267273.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:final,
 pythonExecutable:process.env.MEDIDRONE_RUNTIME_PYTHON??'python3',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:16,requiredNativeTableOwnerSlides:tableOwners,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(build,`validation-${Date.now()}.json`)});
await fs.copyFile(final,destination);
console.log(`Created 16-slide teaching deck with ${tableOwners.length} native tables, all 5 report figures and Turkish speaker notes: ${final}`);
