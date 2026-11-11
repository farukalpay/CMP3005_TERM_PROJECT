## 1. MediDrone Istanbul

Açılış: Hangi drone hangi klinikleri hangi sırayla ziyaret etsin? Sunumda problemi küçük örnekle açıklayıp yöntemleri ve kayıtlı sonuçları karşılaştıracağım. Yaklaşık 12–15 dakika.

Kaynak: report/main.pdf

## 2. The delivery problem

Depo merkezde. Kesikli çizgi sentetik Boğaz sınırı. Her klinik bir kez ziyaret edilmeli, drone kapasitesi ve toplam drone sayısı aşılmamalı. Bu harita gerçek İstanbul koordinatları değil. Renk talebi gösteriyor. Seed 7273 öğrenci numaramın son dört hanesi.

Kaynak: report/main.pdf, Sections 1 and 4; figures/coursework/instance.png

## 3. Why exact optimization is hard

NP üyeliği: rota listesini doğrulamak kolay. İndirgeme yönü zor problemden CVRP’ye. Birinci dönüşümde var olan kenarlar 1, olmayanlar 2 ve eşik N. İkinci dönüşümde tek drone K=1, kapasite n, her talep 1. Bin Packing için örnek 6,6,6 talep, iki adet 10 kapasiteli drone: toplam kapasite yeterli görünse de sığmaz.

Kaynak: report/main.pdf

## 4. Clarke–Wright savings

Başlangıçta her klinik ayrı rota. A ve B’yi birleştirdiğimde depoya giden iki bağlantının yerine A–B geliyor. Tasarruf 17. Yük uygunsa ve uygun rota uçlarıysa birleştiriyoruz. Yöntem her rota için kapasiteyi korur fakat toplam filo sınırını garanti etmez.

Kaynak: report/main.pdf, Section 5; Clarke & Wright (1964)

## 5. Genetic Algorithm

Kromozom klinik sırası; rota ayırıcı yok. Tournament ile ebeveynler seçiliyor. OX her kliniğin bir kez kalmasını sağlıyor. Mutasyon sıra üzerinde değişiklik yapıyor. Split rotalara ayırıyor. Kopyaları elemek ve kısmi restart çeşitliliğe yardımcı. En iyi geçerli sonuç ayrı tutuluyor.

Kaynak: report/main.pdf, Sections 5–6; solver/src/ga.cpp

## 6. Split DP with three clinics

Bu örnek rapordakiyle aynı. Depo 0, klinikler doğru üzerinde 1,2,3. Talepler 4,3,4, kapasite 7. Birinci kesme 10, ikinci kesme 8. D[j] ilk j kliniği servis etmenin en ucuz maliyeti. Son rotanın olası başlangıçlarını deniyoruz. Temel DP O(n²), rota uzunluğu L sınırlıysa O(nL). Koddaki hızlı kuyruk sürümü aynı kesme problemini hızlandırıyor.

Kaynak: report/main.pdf

## 7. Tabu Search

TS tek rota planını değiştiriyor. Dört hamle relocate swap 2opt 2optstar. Silinen kenarlar 10–25 adım tabu oluyor. Yeni en iyi geçerli çözüm bulunacaksa aspiration yasağı kaldırıyor. Geçici aşırı yük cezayla mümkün, son kayıt mutlaka geçerli. Delta altı kenar terimi kullandığı için O(1); hamleyi uygulamak ayrıca maliyetli olabilir.

Kaynak: report/main.pdf, Section 7; solver/src/tabu.cpp

## 8. A fair comparison

Bu tabloyu sonuçlardan önce anlat. Her yöntemin aynı örnekte aynı zamanı var. 1–10 değerlendirme seedleri, 101–105 tuning için ayrı. CW deterministik bir kez. Küçük örneklerde exact sonuç önceden hesaplandı, bu sunum için tekrar deney yok. Runtime ile en iyi cevabın bulunduğu zamanı karıştırma.

Kaynak: report/main.pdf, Section 4; experiments/common.py

## 9. Benchmark results

Maliyetler küçük olduğunda daha iyi. Ortalama tek şanslı koşudan daha anlamlı. SD farklı seedler arasındaki dağılım. TS ilk üç örnekte her koşuda BKS’ye ulaşıyor, son örnekte 6/10. Saf GA ortalama olarak geride. Bu sonuç bütün GA ve TS türleri için evrensel üstünlük kanıtı değil.

Kaynak: report/main.pdf, Section 9; results/coursework/main.csv

## 10. Results on the 100-clinic team instance

Burada referans kanıtlanmış optimum değil kayıtlı en iyi değer 20724.21095. CW 19 rota kullanıyor K18 olduğu için geçersiz, gap vermiyoruz. TS ortalama 20725.5 ve 9/10 koşuda referans. GA ortalama 21352.2. Ucuz görünen ama kısıtları bozan cevabı başarı saymıyoruz.

Kaynak: report/main.pdf, Sections 9–10; results/coursework/main.csv

## 11. Tiny cases with known exact answers

Dokuz örneğin her birinde 10 koşu var. GA için 90, TS için 90 başarılı koşu. DP ve MILP kayıtlı optimumları uyuşuyor. Bu küçük boyutta doğrulama sağlar, büyük problemlerin optimum çözüldüğünü kanıtlamaz.

Kaynak: report/main.pdf, Section 9; results/coursework/tiny.csv

## 12. How quickly do the methods improve?

Grafik A-n45-k6 için. Yatay eksen logaritmik zaman. Çizgi10koşunun medyanı, gölge ortadaki yüzde50. Kayıtlı en iyi cevap azaldıkça çizgi düşüyor. TS erken iyi cevap buluyor. Arama sırasında mevcut çözüm kötüleşebilir ama best-so-far asla artmaz.

Kaynak: report/main.pdf, Section 10; figures/coursework/convergence.png

## 13. The final team delivery plan

Renkler farklı drone rotaları. Plan 17 drone kullanıyor. 10 rota Avrupa’ya gidip geliyor: toplam 20 geçiş. Avrupa talebi 938, her drone 100 taşıyor, en az 10 drone gerekiyor. Bu plan geçiş sayısında alt sınıra ulaşıyor, toplam mesafe optimumluğu ayrı bir konu.

Kaynak: report/main.pdf, Section 10; figures/coursework/routes.png

## 14. Complexity checked against measurements

Sol grafik log-log. Sabit20aday TS lineer bekleniyor eğim1.08; bütün adaylar kuadratik eğim2.12. GA50popülasyonda0.84; sabit giderler küçük boyutta etkili. Sağda delta bütün çözümü tekrar toplamaktan çok ucuz. Ölçülen eğim ispat değil teorik analize destek.3200 noktasındaki TS sıçraması cache ve bellek etkisiyle uyumlu, kesin sebep iddiası yok.

Kaynak: report/main.pdf, Section 8; figures/coursework/complexity.png

## 15. Parameter choice and crossing penalties

Solda çok kısa tabu hemen geri dönmeye izin veriyor, çok uzun tabu yararlı hareketi kısıtlıyor.10–25 iyi bir orta bölge. Sağda P 0’dan 1000’e artsa da 10 geçiş rotası değişmiyor. Rotalar zaten kapasitenin zorunlu minimumuna ulaştığı için ceza artırmak yapıyı değiştirmiyor. Olmamış etkiyi olmuş gibi anlatmıyoruz.

Kaynak: report/main.pdf, Section 11; figures/coursework/sensitivity.png

## 16. What the results support

Sonuçları sınırlarıyla özetle. TS bu implementasyonlarda daha iyi ortalama. Küçük örnekler ve bağımsız checker doğrulamaya yardımcı. Model sentetik koordinatlar ve yük kapasitesi kullanıyor. Batarya, rüzgar, uçuş izinleri ve zaman pencereleri yok. Gelecekte GA’ya local search eklemek mantıklı, mevcut MA kodu var. Sorularda Split örneğine veya TS delta formülüne geri dön.

Kaynak: report/main.pdf, Sections 11–12
