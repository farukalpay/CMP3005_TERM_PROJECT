# MediDrone: anlama ve sözlü savunma rehberi

Projenin temel sorusu şu: **Hangi drone hangi kliniklere, hangi sırayla gitsin?** Her kliniğe bir kez uğranacak, yük sınırı aşılmayacak ve bütün drone'lar laboratuvara dönecek. Boğaz geçişi ek maliyet getiriyor.

Önce bu dosyayı, sonra [İngilizce raporu](../deliverables/CMP3005_Report_FarukAlpay_2267273.pdf), ardından [kod haritasını](CODE_MAP.md) oku. Ek araştırma raporu, gerçek İstanbul verisi ve geniş benchmarklar ana projeyi anlamak için başlangıç noktası değil.

## 1. En küçük örnek

Bir drone en fazla 10 birim taşısın. A, B, C kliniklerinin talepleri 4, 5, 3 olsun.

- A ve B aynı drone'a verilebilir: yük 9.
- Üçü aynı drone'a verilemez: yük 12.
- İki drone varsa `Lab → A → B → Lab` ve `Lab → C → Lab` geçerli bir plan olabilir.

Önce **plan geçerli mi**, sonra **maliyeti ne** diye bakıyoruz. Ucuz ama yük sınırını aşan plan başarılı sonuç sayılmaz. Aynı şekilde drone sayısı sınırını aşmak da planı geçersiz yapar.

## 2. Bilmen gereken semboller

| Sembol / terim | Anlamı |
|---|---|
| `n` | Klinik sayısı; depo buna dahil değil |
| `q_i` | i kliniğinin istediği yük |
| `Q` | Bir drone'un taşıma kapasitesi |
| `K` | Kullanılabilecek en fazla drone sayısı |
| `d(i,j)` | İki nokta arasındaki maliyet |
| `P` | Tek Boğaz geçişi için ek maliyet |
| `B` | Karar problemindeki toplam maliyet eşiği |
| `μ` | GA'daki aday çözüm sayısı, yani popülasyon |
| `k` | TS'de bakılan yakın komşu sayısı; filo sınırı `K` ile farklı |
| BKS | Benchmark için yayımlanmış en iyi bilinen değer |
| seed | Rastgele seçimleri belirleyen sayı |
| gap | Referans maliyetten yüzde olarak ne kadar uzaktayız |

Örneğin maliyet 105, referans 100 ise gap %5'tir. Takım örneğinin referansı ispatlanmış optimum değil, mevcut deneylerde bulunan en iyi değerdir. Sentetik haritadaki birimlere kilometre demiyoruz.

## 3. Hocanın istediği matematik ne anlatıyor?

### NP üyeliği: verilen cevabı kontrol edebiliyor muyuz?

Evet. Rotaları tara, her kliniğin bir kez geçtiğini, yükleri, drone sayısını ve maliyeti kontrol et. Her kliniğe sabit miktarda iş yapınca kontrol `O(n)` olur. Mesafe tablosunu önceden oluşturmanın maliyeti ayrıca `O(n²)`.

**Kolay kontrol etmek, kolay bulmak demek değil.** Bir Sudoku cevabını kontrol etmek ile cevabı baştan bulmak arasındaki ayrım gibi düşün.

### Hamiltonian Cycle → TSP → CVRP

İndirgeme, bir problemi başka bir problemin girdisine dönüştürüp EVET/HAYIR cevabını korumaktır. İki yönde de neden korunduğunu anlatabilmelisin.

1. Bir grafın var olan kenarlarına 1, olmayanlara 2 maliyet ver. `N` düğümlük bir turun maliyeti en fazla `N` ise bütün kenarlar 1 olmalıdır. Yani tur, başlangıç grafındaki kenarlardan oluşur.
2. TSP'yi CVRP yapmak için tek drone koy: `K=1`. Her kliniğin talebi 1, drone kapasitesi `Q=n` olsun. Kapasite sorun olmaktan çıkar. Tek drone bütün klinikleri gezmek zorunda kalır; bu da TSP olur.

Zor olduğu bilinen problemden CVRP'ye gidiyoruz. Ters yöndeki bir dönüşüm aynı sonucu kanıtlamaz. İki dönüşüm de polinom zamanda yapıldığı için arka arkaya uygulamak da polinom zamandır.

### Bin Packing neden burada?

Mesafeyi unut. Yükleri drone'lara sığdırmak, eşyaları kutulara sığdırmakla aynı problem. Talepler `6,6,6`, kapasite 10, drone sayısı 2 olsun. Toplam yük 18, toplam kapasite 20 olmasına rağmen çözüm yok: iki adet 6 aynı drone'a sığmıyor. Yalnız toplam kapasite hesabı yapmak yeterli değil.

### Boğaz cezası neden üçgen eşitsizliğini koruyor?

Farklı yakalardaki iki noktaya doğrudan giderken bir geçiş ödüyorsan, üçüncü bir noktadan dolaşırken de en az bir kez karşıya geçmelisin. Dolanmak geçişi yok edemez. Normal mesafe zaten üçgen eşitsizliğini sağlıyor; sabit geçiş cezası eklemek bunu bozmuyor.

## 4. Clarke–Wright: önce basit bir plan

Başlangıçta her kliniğe ayrı drone gönder. İki rotayı birleştirmenin ne kadar tasarruf ettireceğini hesapla. En çok tasarruf sağlayan uygun birleşmeyi önce dene.

Depodan A'ya maliyet 10, depodan B'ye 12, A–B arası 5 ise birleştirme tasarrufu `10+12−5=17` olur. Yük uygunsa ve rota uçları birleştirilebiliyorsa birleştir.

Bu yöntem hızlıdır ama yanlış bir erken tercihi geri almaz. Bu projede bazı sonuçlarında fazla drone gerekiyor. “Her rota kapasiteye uyuyor” ile “plan filoya uyuyor” ayrı kontroller.

Kod: `solver/src/savings.cpp`.

## 5. GA: çok sayıda ziyaret sırasını denemek

Bir aday `[3,1,4,2]` gibi klinik sıralamasıdır. Buna kromozom deniyor. Henüz drone ayrımları yok.

- **Seçim:** İki rastgele adayı karşılaştırıp iyisini ebeveyn seç.
- **Crossover:** İki sıradan yeni bir sıra üret, her klinik yine bir kez bulunsun.
- **Mutasyon:** İki kliniği değiştir, bir parçayı ters çevir veya bir kliniği taşı.
- **Split:** Bu sırayı yük sınırına uygun rotalara böl.
- **Replacement:** Yeni adayı popülasyona yerleştirirken en iyi cevabı koru.

Her nesil yaklaşık `μ` yeni aday dener. Tekrarlanan çözümleri elemek ve uzun durgunlukta popülasyonun bir kısmını yenilemek çeşitliliğe yardımcı olur. Mutasyon olasılığı 1, bütün sıranın rastgeleleşmesi değil, her çocukta bir mutasyon uygulanması demektir.

Kod: `solver/src/ga.cpp`. Önce `decode`, sonra `tournament`, `ox`, `mutate` ve ana döngüyü oku.

## 6. Split DP: sadece kesme yerlerini seçiyor

Sıra `[1,2,3]`, talepler `[4,3,4]`, kapasite 7 olsun. `[1,2] | [3]` ve `[1] | [2,3]` geçerlidir. Üçünü birden aynı drone'a koyamayız.

Depo bir sayı doğrusunda 0'da, klinikler 1, 2, 3 noktalarında olsun. İlk kesme toplam 10, ikinci kesme toplam 8 maliyet verir. Split ikinciyi seçer.

`D[j]`, sıranın ilk `j` kliniğini bitirmenin en ucuz maliyetidir. Son rotanın nereden başladığını sırayla denersin:

```text
D[0] = 0
D[j] = min(D[i] + i+1 ... j kliniklerini tek rotada gezmenin maliyeti)
       yalnız yükü kapasiteye sığan bloklar için
```

`n` bitiş yeri için en fazla `n` başlangıç denenir: `O(n²)`. Bir rotaya en fazla `L` klinik sığıyorsa `O(nL)` olur. Drone sayısını da sınırlamak için duruma kullanılan rota sayısını ekleriz.

Mevcut kodda ayrıca daha hızlı bir kuyruk optimizasyonu var. İlk öğrenilecek şey yukarıdaki temel DP. Hızlı sürümün her elemanı kuyruğa bir kez girip çıkardığı fikrini ve filo sınırlı sürümün `K` katman kullandığını da bilmelisin. Rapor kodda bu farkı açıkça söylüyor; kodun temel DP'yi kullandığını iddia etmiyor.

Hızlı sürümün sezgisi şöyle: Bir bitiş kliniği için bütün başlangıçları yeniden taramak yerine, işe yarayabilecek başlangıçları bir kuyrukta tutuyoruz. Çok eski bir başlangıç kapasiteyi aştıysa önden çıkar. Yeni bir başlangıç eskisinden daha ucuzsa ve kapasite açısından en az onun kadar uzun süre kullanılabilecekse, eski pahalı aday arkadan çıkar. Her başlangıç bir kez girip en fazla bir kez çıktığından toplam kuyruk işi `O(n)` olur. `SQ` birikmiş talepleri, `SD` sıra boyunca birikmiş mesafeyi tutar; `phi` başlangıca bağlı maliyet kısmıdır. Kodda `front` ve `back` hareketlerini bu açıklamayla eşleştir.

Kod: `solver/src/split.cpp`, önce `split_bellman`, sonra `split_linear` ve `split_limited`.

**En önemli sınır:** Split, verilen sıra için en iyi kesmeyi bulur. Bütün CVRP'nin optimumunu bulmuş olmaz.

## 7. TS: tek plan üzerinde küçük değişiklikler

TS, hazır rotalarla başlar. Bir kliniği başka rotaya taşır, iki kliniği değiştirir, rota parçasını ters çevirir veya iki rotanın kuyruklarını değiştirir. CW başlangıcında fazla rota varsa kod klinikleri `K` rota içine yerleştirir; geçici aşırı yük oluşabilir.

TS sadece her zaman ucuzlayan hamleleri seçse yerel bir noktada takılabilir. Bazen maliyeti artıran hamleye de gider, ama bulduğu en iyi **geçerli** cevabı ayrı tutar.

**Tabu listesi:** Silinen kenarları kısa süreliğine geri eklemeyi yasaklar. Böylece hemen geri dönme eğilimini azaltır. **Aspiration:** Yasak hamle yeni en iyi geçerli cevabı buluyorsa izin verilir.

**Kapasite cezası:** Geçici aşırı yüke `λ × aşırı yük` eklenir. Plan aşırı yüklüyse ceza büyür, geçerliyse küçülür. Sonuç diye kaydedilen plan yine kapasite ve drone sayısı şartlarını sağlamalıdır.

**Delta evaluation:** Bir kliniği taşımada sadece değişen birkaç kenarı hesaplarız. Bütün rotaları tekrar toplamayız. Altı mesafe terimi kullanan relocate formülü bu yüzden `O(1)`'dir. Hamlenin etkisini hesaplamak ile dizileri güncelleyerek hamleyi uygulamak aynı maliyet değildir.

Kod: `solver/src/tabu.cpp`, hamleler için `solver/src/routes.hpp`.

## 8. Karmaşıklığı nasıl anlatırsın?

| İş | Neden bu maliyet? |
|---|---|
| CW: `O(n² log n)` | Yaklaşık `n²` tasarrufu sıralıyor |
| Temel Split: `O(nL)` | Her bitiş için en fazla `L` başlangıç |
| GA nesli: olağan durumda `O(μ(n+μ))` | `μ` çocuk; her çocukta sıra işlemleri ve popülasyon yerleştirmesi |
| GA filo sınırlı Split gerekirse | Çocuk başına decoding `O(Kn)` olabilir |
| TS adımı: `O(nk)` | `n` klinik, her birinde yaklaşık `k` yakın aday |
| TS bütün komşulara bakarsa: `O(n²)` | `k` de `n` ile büyür |

Grafikte ölçülen eğimler yaklaşık 1.08, 2.12 ve 0.84. Bunlar her girdi için kesin ispat değil. Küçük girdilerde sabit masraflar, büyüklerde bellek/cache etkileri var. Bir adımın maliyeti ile iyi çözüme ulaşmak için gereken adım sayısını karıştırma.

## 9. Sonuçlardan dürüstçe ne diyebiliriz?

Bu ayarlarla TS'nin ortalama maliyeti beş ana örnekte de saf GA'dan düşük. “TS her zaman GA'dan iyidir” sonucu çıkmaz. Dokuz küçük örnekte iki yöntem de her çalışmada optimuma ulaşıyor; bu büyük örneklerin optimum olduğunu kanıtlamaz.

Takım örneğinde en iyi kayıtlı TS planı 17 drone kullanıyor. 10 rota Avrupa'ya geçiyor, her biri gidiş-dönüş iki geçiş yapıyor. Avrupa talebi 938 ve kapasite 100 olduğundan zaten en az 10 drone gerekiyor. Geçiş sayısında bu alt sınıra ulaşılıyor. Toplam rota maliyetinin optimumluğu ayrıca ispatlanmış değil.

Boğaz cezası artınca sentetik örneğin en iyi kayıtlı rota yapısı değişmiyor. Bunu değiştirmiş gibi anlatma. Mevcut çözüm, geçiş sayısını kapasitenin gerektirdiği seviyeye zaten indirmiş.

## 10. 10–15 dakikalık sunum akışı

| Süre | Anlatılacak şey |
|---|---|
| 0–1 dk | Küçük yük örneğiyle problem ve geçerli çözüm |
| 1–3 dk | İndirgeme zinciri, Bin Packing ve ceza sezgisi |
| 3–4 dk | CW tasarrufu ve sınırlaması |
| 4–6 dk | GA ve üç kliniklik Split örneği |
| 6–8 dk | TS, tabu hafızası, bir relocate hamlesi |
| 8–10 dk | Aynı süre/10 seed, ana sonuç ve rota haritası |
| 10–12 dk | Karmaşıklık, bir parametre grafiği, sınırlamalar |

Güncel 16 slaytlık PPTX `deliverables/` klasöründe. Tablolar, sonuç yorumları, rapor figürleri ve küçük algoritma örnekleri içerir. Türkçe konuşmacı notları PPTX içinde ve `slides/speaker_notes_TR.md` dosyasında bulunur. Eski Beamer dosyası ayrı bir araştırma sürümüdür.

## 11. Kendini sınayacağın sorular

1. Kısa bir rota hangi iki farklı nedenle geçersiz olabilir?
2. TSP'yi CVRP'ye çevirirken neden `Q=n`, `K=1`, `q_i=1` seçiyoruz?
3. Split hangi şeyi optimize ediyor, hangi şeyi etmiyor?
4. OX'ten sonra bir kliniğin iki kez bulunmasını nasıl engelliyoruz?
5. GA en iyi bireyi nasıl koruyor, TS en iyi cevabı nasıl saklıyor?
6. Neden TS bazen daha pahalı veya aşırı yüklü bir duruma gidiyor?
7. `O(1)` hamle değerlendirmesi, neden bütün TS adımının `O(1)` olduğu anlamına gelmiyor?
8. 20,724.21095 için neden “kesin optimum” diyemiyoruz?
9. Çok yüksek Boğaz cezası burada neden rota değişikliği yaratmıyor?
10. Deneyleri yeniden çalıştırmadan bir tablonun sayısını hangi JSON'dan kontrol edersin?

Bu soruları kendi cümlelerinle ve ilgili kodu göstererek cevaplamaya çalış. Açıklayamadığın ek bir yöntemi sunumun merkezine koyma. Raporun AI beyanını ve kişisel hata/öğrenme anlatısını da gerçek çalışma sürecinle karşılaştırarak düzelt.
