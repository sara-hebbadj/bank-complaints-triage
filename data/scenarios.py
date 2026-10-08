"""100 synthetic customer-message scenarios, each written in English, Arabic and French (300 messages).

Written by a coding agent (Claude) on 8 October 2026 for the fictional "Gulf Horizon Bank". The Arabic and
French texts are NOT yet reviewed by a native speaker. Arabic varieties: Modern Standard Arabic ("msa"),
Gulf dialect ("gulf") and Arabizi, Arabic written in Latin letters and digits ("arabizi").

Labels (gold, set by the author of the scenario):
- topic: the team that owns the subject. The final gold team follows the routing rule in code:
  fraud -> fraud_security, else vulnerable -> customer_care, else dispute -> disputes, else topic.
- complaint: the customer expresses dissatisfaction with something the bank did or failed to do and expects
  a fix, refund or answer. A neutral question or request is not a complaint. Every card dispute counts as a
  complaint (fictional bank policy, clause 5.1).
- dispute: the customer contests a specific card or ATM transaction.
- reason: the gold reason code (taxonomy.REASON_CODES) for complaints and fraud reports, else None.
"""

S = []


def s(topic, en, ar, fr, complaint=False, dispute=False, fraud=False, vuln=False, reason=None, variety="msa"):
    S.append({"topic": topic, "en": en, "ar": ar, "fr": fr, "complaint": complaint or dispute, "dispute": dispute,
              "fraud": fraud, "vulnerable": vuln, "reason": reason, "ar_variety": variety})


# ---------------- cards (13) ----------------
s("cards", "How do I activate the new card you sent me?",
  "كيف يمكنني تفعيل البطاقة الجديدة التي أرسلتموها لي؟",
  "Comment activer la nouvelle carte que vous m'avez envoyée ?")
s("cards", "My card STILL hasn't arrived. I ordered it three weeks ago and this is the second time I'm chasing you. Very disappointed.",
  "طلبت البطاقة من ثلاث أسابيع وللحين ما وصلت، وهذي ثاني مرة أتابع معكم. والله شي مخيب.",
  "Ma carte n'est TOUJOURS pas arrivée. Je l'ai commandée il y a trois semaines et c'est la deuxième fois que je vous relance. Très déçue.",
  complaint=True, reason="RC-DLY", variety="gulf")
s("cards", "Can I add my Gulf Horizon card to Apple Pay or Google Pay?",
  "هل يمكنني إضافة بطاقة بنك الأفق الخليجي إلى Apple Pay أو Google Pay؟",
  "Est-ce que je peux ajouter ma carte Gulf Horizon à Apple Pay ou Google Pay ?")
s("cards", "My card expires next month. Will you send me a new one automatically?",
  "بطاقتي تنتهي الشهر الجاي، بترسلون لي وحدة جديدة تلقائياً؟",
  "Ma carte expire le mois prochain. Est-ce que vous m'en envoyez une nouvelle automatiquement ?", variety="gulf")
s("cards", "Contactless hasn't worked on my card for a month. I reported it twice in the app and nothing happened. Please fix it properly this time.",
  "الدفع اللاتلامسي لا يعمل على بطاقتي منذ شهر. أبلغت عن المشكلة مرتين في التطبيق ولم يحدث شيء. أرجو حلها هذه المرة.",
  "Le sans contact ne fonctionne plus sur ma carte depuis un mois. Je l'ai signalé deux fois dans l'application et rien n'a été fait. Merci de régler ça cette fois.",
  complaint=True, reason="RC-SVC")
s("cards", "I'd like to change my PIN. Can I do it in the app?",
  "أبغى أغير الرقم السري حق البطاقة، أقدر أسويها من التطبيق؟",
  "Je voudrais changer mon code PIN. Est-ce possible dans l'application ?", variety="gulf")
s("cards", "I typed the wrong PIN three times and now it's blocked. How do I unblock it?",
  "ktabt el PIN ghalat 3 marrat w sar blocked, kaif afti7a?",
  "J'ai tapé trois fois le mauvais code et ma carte est bloquée. Comment la débloquer ?", variety="arabizi")
s("cards", "I need a virtual card for online shopping. How do I get one?",
  "أحتاج إلى بطاقة افتراضية للتسوق عبر الإنترنت، كيف أحصل عليها؟",
  "J'ai besoin d'une carte virtuelle pour mes achats en ligne. Comment en obtenir une ?")
s("cards", "My card was declined at the supermarket today even though I have plenty of money in the account. It was embarrassing and nobody can explain why. I want an explanation.",
  "رُفضت بطاقتي اليوم في السوبرماركت رغم أن رصيدي كافٍ. كان موقفاً محرجاً ولم يستطع أحد أن يشرح لي السبب. أريد تفسيراً.",
  "Ma carte a été refusée au supermarché aujourd'hui alors que j'ai largement assez sur mon compte. C'était humiliant et personne ne sait m'expliquer pourquoi. J'exige une explication.",
  complaint=True, reason="RC-SVC")
s("cards", "I ordered a physical card. How long does delivery usually take?",
  "طلبت بطاقة بلاستيك، كم يوم ياخذ التوصيل عادة؟",
  "J'ai commandé une carte physique. Combien de temps prend la livraison en général ?", variety="gulf")
s("cards", "Is my debit card a Visa or a Mastercard?",
  "هل بطاقة الخصم الخاصة بي فيزا أم ماستركارد؟",
  "Ma carte de débit, c'est une Visa ou une Mastercard ?")
s("cards", "Your app keeps saying my card 'is not working' for online payments. I've tried five times today. Fix this now, I have bills to pay.",
  "التطبيق مالكم كل شوي يقول إن البطاقة ما تشتغل للدفع أونلاين. جربت خمس مرات اليوم. صلحوها الحين، عندي فواتير لازم أدفعها.",
  "Votre application affiche sans arrêt que ma carte « ne fonctionne pas » pour les paiements en ligne. J'ai essayé cinq fois aujourd'hui. Réglez ça tout de suite, j'ai des factures à payer.",
  complaint=True, reason="RC-SVC", variety="gulf")
s("cards", "Can I get a second card on my account for my wife?",
  "هل يمكنني الحصول على بطاقة إضافية على حسابي لزوجتي؟",
  "Est-ce que je peux avoir une deuxième carte sur mon compte pour mon épouse ?")

# ---------------- payments (13) ----------------
s("payments", "How long does an international transfer to India take?",
  "كم يستغرق التحويل الدولي إلى الهند؟",
  "Combien de temps prend un virement international vers l'Inde ?")
s("payments", "My transfer to my brother in Egypt has been pending for five days. He needs the money for his rent and I'm really unhappy with this delay.",
  "تحويلي لأخوي في مصر معلق من خمسة أيام. يحتاج الفلوس للإيجار وأنا مب راضي أبد عن هالتأخير.",
  "Mon virement vers mon frère en Égypte est en attente depuis cinq jours. Il a besoin de cet argent pour son loyer et je suis vraiment mécontent de ce retard.",
  complaint=True, reason="RC-PAY", variety="gulf")
s("payments", "I just sent a transfer to the wrong account number. Can I cancel it?",
  "أرسلت للتو تحويلاً إلى رقم حساب خاطئ. هل يمكنني إلغاؤه؟",
  "Je viens d'envoyer un virement sur un mauvais numéro de compte. Est-ce que je peux l'annuler ?")
s("payments", "The transfer failed but the money has left my account! I want it back in my account immediately.",
  "فشل التحويل لكن المبلغ خُصم من حسابي! أريد إعادته إلى حسابي فوراً.",
  "Le virement a échoué mais l'argent a quand même quitté mon compte ! Je veux qu'il soit recrédité immédiatement.",
  complaint=True, reason="RC-PAY")
s("payments", "Can I set up an automatic top-up when my balance goes below AED 500?",
  "أقدر أفعّل تعبئة تلقائية للرصيد إذا نزل عن ٥٠٠ درهم؟",
  "Est-ce que je peux mettre en place une recharge automatique quand mon solde passe sous 500 AED ?", variety="gulf")
s("payments", "I topped up by card yesterday and it still shows as pending. Is that normal?",
  "قمت بتعبئة الرصيد بالبطاقة أمس وما زالت العملية معلقة. هل هذا طبيعي؟",
  "J'ai rechargé par carte hier et c'est toujours en attente. C'est normal ?")
s("payments", "My employer says my salary was sent three days ago. When should I see it in my account?",
  "الشركة تقول إنها حولت الراتب قبل ثلاثة أيام. متى بيبين في حسابي؟",
  "Mon employeur dit que mon salaire a été envoyé il y a trois jours. Quand vais-je le voir sur mon compte ?", variety="gulf")
s("payments", "The app says this beneficiary is 'not allowed'. What does that mean?",
  "التطبيق يقول إن هذا المستفيد 'غير مسموح'. ماذا يعني ذلك؟",
  "L'application indique que ce bénéficiaire n'est « pas autorisé ». Qu'est-ce que ça veut dire ?")
s("payments", "I've waited a whole week for a bank transfer to show in my balance. This is unacceptable. I had to pay late fees on my bills and I want compensation.",
  "انتظرت أسبوعاً كاملاً حتى يظهر التحويل في رصيدي. هذا غير مقبول. اضطررت لدفع غرامات تأخير على فواتيري وأطالب بتعويض.",
  "J'attends depuis une semaine entière qu'un virement apparaisse sur mon solde. C'est inacceptable. J'ai dû payer des pénalités de retard sur mes factures et je demande une compensation.",
  complaint=True, reason="RC-PAY")
s("payments", "Can I top up my account with cash or a cheque at a branch?",
  "هل يمكنني إيداع نقد أو شيك في فرع لتعبئة حسابي؟",
  "Puis-je alimenter mon compte en espèces ou par chèque en agence ?")
s("payments", "My top-up was reverted and nobody told me. This is the third time this month. Terrible service.",
  "التعبئة رجعت وما حد خبرني. هذي ثالث مرة هالشهر. خدمة سيئة.",
  "Ma recharge a été annulée et personne ne m'a prévenu. C'est la troisième fois ce mois-ci. Service lamentable.",
  complaint=True, reason="RC-PAY", variety="gulf")
s("payments", "How long does a transfer between two Gulf Horizon accounts take to arrive?",
  "kam ya5ith el transfer bain 2 7sabat fi Gulf Horizon 7atta yewsal?",
  "Combien de temps faut-il pour un virement entre deux comptes Gulf Horizon ?", variety="arabizi")
s("payments", "The money I sent to my landlord on Sunday never arrived and he's threatening to cancel my lease. I need this sorted today, this is your mistake.",
  "المبلغ الذي أرسلته لمالك الشقة يوم الأحد لم يصل، وهو يهدد بإلغاء عقد الإيجار. أحتاج حل المشكلة اليوم، فالخطأ خطؤكم.",
  "L'argent que j'ai envoyé à mon propriétaire dimanche n'est jamais arrivé et il menace de résilier mon bail. Il faut régler ça aujourd'hui, c'est votre erreur.",
  complaint=True, reason="RC-PAY")

# ---------------- ATM and cash (10) ----------------
s("atm_cash", "The ATM at the mall kept my card. What should I do now?",
  "الصراف الآلي في المول احتجز بطاقتي. ماذا أفعل الآن؟",
  "Le distributeur du centre commercial a avalé ma carte. Que dois-je faire ?")
s("atm_cash", "My cash withdrawal has been showing as pending in the app since Monday.",
  "السحب النقدي معلق في التطبيق من يوم الاثنين.",
  "Mon retrait d'espèces apparaît en attente dans l'application depuis lundi.", variety="gulf")
s("atm_cash", "Why was my cash withdrawal declined when I was travelling in Oman?",
  "لماذا رُفض سحبي النقدي عندما كنت مسافراً في عُمان؟",
  "Pourquoi mon retrait a-t-il été refusé quand j'étais en voyage à Oman ?")
s("atm_cash", "Where is the nearest ATM that takes cash deposits?",
  "وين أقرب صراف يقبل إيداع كاش؟",
  "Où se trouve le distributeur le plus proche qui accepte les dépôts d'espèces ?", variety="gulf")
s("atm_cash", "The ATM swallowed my card AGAIN and the branch told me they can't help. Second time this month. I'm fed up with your machines.",
  "الصراف ابتلع بطاقتي مرة ثانية والفرع قال إنه ما يقدر يساعدني. ثاني مرة هالشهر. طفشت من مكايينكم.",
  "Le distributeur a ENCORE avalé ma carte et l'agence m'a dit qu'elle ne pouvait rien faire. Deuxième fois ce mois-ci. J'en ai assez de vos machines.",
  complaint=True, reason="RC-SVC", variety="gulf")
s("atm_cash", "Your ATM declined my withdrawal three times when I urgently needed cash for a taxi. Really bad experience.",
  "رفض الصراف الآلي التابع لكم سحبي ثلاث مرات بينما كنت بحاجة ماسة إلى النقود لسيارة الأجرة. تجربة سيئة جداً.",
  "Votre distributeur a refusé mon retrait trois fois alors que j'avais un besoin urgent d'espèces pour un taxi. Très mauvaise expérience.",
  complaint=True, reason="RC-SVC")
s("atm_cash", "A withdrawal of AED 800 has been pending for four days and the money is gone from my balance. I want an explanation and my money back.",
  "سحب بقيمة 800 درهم معلق منذ أربعة أيام والمبلغ اختفى من رصيدي. أريد تفسيراً واسترداد أموالي.",
  "Un retrait de 800 AED est en attente depuis quatre jours et l'argent a disparu de mon solde. Je veux une explication et récupérer mon argent.",
  complaint=True, dispute=True, reason="RC-ATM")
s("atm_cash", "Can I use my virtual card to take cash out at an ATM?",
  "momken asta5dem el virtual card 3shan as7ab cash mn el ATM?",
  "Est-ce que je peux utiliser ma carte virtuelle pour retirer des espèces à un distributeur ?", variety="arabizi")
s("atm_cash", "The ATM took my card in Deira. How do I get it back?",
  "el ATM fi Deira 5ad karti, kaif arj3ha?",
  "Le distributeur à Deira a gardé ma carte. Comment la récupérer ?", variety="arabizi")
s("atm_cash", "Is there a daily limit on how much cash I can withdraw?",
  "هل يوجد حد يومي للمبلغ الذي يمكنني سحبه نقداً؟",
  "Y a-t-il une limite quotidienne de retrait d'espèces ?")

# ---------------- fees and exchange rates (12) ----------------
s("fees_fx", "Why was I charged a fee for a card payment yesterday?",
  "لماذا تم احتساب رسوم على دفعة بالبطاقة أمس؟",
  "Pourquoi ai-je payé des frais sur un paiement par carte hier ?")
s("fees_fx", "You charged me AED 25 for a transfer that your website says is free. This is a rip-off. Refund the fee.",
  "خصمتوا مني 25 درهم على تحويل موقعكم يقول إنه مجاني. هذا نصب. رجعوا الرسوم.",
  "Vous m'avez facturé 25 AED pour un virement que votre site présente comme gratuit. C'est du vol. Remboursez ces frais.",
  complaint=True, reason="RC-FEE", variety="gulf")
s("fees_fx", "What exchange rate do you use for US dollars?",
  "ما هو سعر الصرف الذي تستخدمونه للدولار الأمريكي؟",
  "Quel taux de change appliquez-vous pour le dollar américain ?")
s("fees_fx", "The exchange rate on my card payment in London was far worse than the official rate. I feel cheated and I want the difference back.",
  "سعر الصرف على دفعتي بالبطاقة في لندن كان أسوأ بكثير من السعر الرسمي. أشعر بأنني تعرضت للغش وأريد استرداد الفرق.",
  "Le taux de change sur mon paiement par carte à Londres était bien pire que le taux officiel. Je me sens floué et je veux récupérer la différence.",
  complaint=True, reason="RC-FEE")
s("fees_fx", "Is there a charge for topping up by debit card?",
  "في رسوم إذا عبيت الرصيد ببطاقة الخصم؟",
  "Y a-t-il des frais pour une recharge par carte de débit ?", variety="gulf")
s("fees_fx", "There's an extra AED 15 charge on my statement and I don't know what it is. Can you tell me?",
  "توجد رسوم إضافية بقيمة 15 درهماً في كشف حسابي ولا أعرف ما هي. هل يمكنكم توضيحها؟",
  "Il y a un débit supplémentaire de 15 AED sur mon relevé et je ne sais pas ce que c'est. Pouvez-vous me renseigner ?")
s("fees_fx", "Hidden fees again! A AED 12 cash withdrawal charge that nobody told me about. I want it reversed.",
  "رسوم مخفية مرة ثانية! 12 درهم على سحب كاش وما أحد قال لي. أبغاها ترجع.",
  "Encore des frais cachés ! 12 AED de frais de retrait dont personne ne m'a parlé. Je veux qu'ils soient annulés.",
  complaint=True, reason="RC-FEE", variety="gulf")
s("fees_fx", "How much do you charge to exchange money in the app?",
  "كم الرسوم على تحويل العملات في التطبيق؟",
  "Combien coûte le change de devises dans l'application ?", variety="gulf")
s("fees_fx", "Which currencies can I hold in my account?",
  "ما هي العملات التي يمكنني الاحتفاظ بها في حسابي؟",
  "Quelles devises puis-je détenir sur mon compte ?")
s("fees_fx", "I was charged an exchange fee on a payment that was in dirhams. That's wrong, please refund it.",
  "تم خصم رسوم صرف عملة على دفعة كانت بالدرهم. هذا خطأ، أرجو استرداد الرسوم.",
  "On m'a prélevé des frais de change sur un paiement en dirhams. C'est une erreur, merci de me rembourser.",
  complaint=True, reason="RC-FEE")
s("fees_fx", "Why did you take a fee for my transfer?",
  "lesh 5athtou mni fee 3ala el transfer?",
  "Pourquoi avez-vous pris des frais sur mon virement ?", variety="arabizi")
s("fees_fx", "Your fees are the highest in the market and your staff couldn't even explain them. I want to make a formal complaint.",
  "رسومكم هي الأعلى في السوق وموظفوكم لم يتمكنوا حتى من شرحها. أريد تقديم شكوى رسمية.",
  "Vos frais sont les plus élevés du marché et votre personnel n'a même pas su les expliquer. Je souhaite déposer une réclamation officielle.",
  complaint=True, reason="RC-FEE")

# ---------------- card disputes (14) ----------------
s("disputes", "I was charged twice for the same dinner at Desert Bloom Café on 2 October, AED 186 each time. Please reverse one of them.",
  "انخصم مني مرتين على نفس العشاء في ديزرت بلوم كافيه يوم 2 أكتوبر، 186 درهم كل مرة. رجعوا وحدة منهم لو سمحتوا.",
  "On m'a débité deux fois le même dîner au Desert Bloom Café le 2 octobre, 186 AED chaque fois. Merci d'annuler l'un des deux.",
  dispute=True, reason="RC-DUP", variety="gulf")
s("disputes", "I paid FurniHome AED 2,300 for a sofa on 15 September. It was never delivered and the shop doesn't answer the phone.",
  "دفعت لمتجر فيرني هوم 2300 درهم ثمن أريكة في 15 سبتمبر، ولم يتم توصيلها أبداً والمتجر لا يرد على الهاتف.",
  "J'ai payé 2 300 AED à FurniHome pour un canapé le 15 septembre. Il n'a jamais été livré et le magasin ne répond plus.",
  dispute=True, reason="RC-NRV")
s("disputes", "I returned a jacket to Bayview Fashion and they say the refund was processed two weeks ago. I still have nothing on my card.",
  "أرجعت جاكيت لمحل بايفيو فاشن ويقولون إن المبلغ رجع من أسبوعين، بس للحين ما وصلني شي على البطاقة.",
  "J'ai rendu une veste chez Bayview Fashion et ils disent que le remboursement a été fait il y a deux semaines. Je n'ai toujours rien sur ma carte.",
  dispute=True, reason="RC-RFD", variety="gulf")
s("disputes", "I cancelled my StreamMax subscription in August, but you still charged me AED 39 this month.",
  "ألغيت اشتراكي في ستريم ماكس في أغسطس، ومع ذلك خصمتم 39 درهماً هذا الشهر.",
  "J'ai résilié mon abonnement StreamMax en août, mais vous m'avez quand même prélevé 39 AED ce mois-ci.",
  dispute=True, reason="RC-SUB")
s("disputes", "The restaurant charged my card AED 450 instead of AED 45. Can you get the difference back?",
  "المطعم خصم من بطاقتي 450 درهماً بدلاً من 45 درهماً. هل يمكنكم استرجاع الفرق؟",
  "Le restaurant a débité 450 AED au lieu de 45 AED sur ma carte. Pouvez-vous récupérer la différence ?",
  dispute=True, reason="RC-AMT")
s("disputes", "I withdrew AED 1,000 but the ATM only gave me AED 500. I want the rest back.",
  "سحبت 1000 درهم بس الصراف عطاني 500 بس. أبغى الباقي.",
  "J'ai retiré 1 000 AED mais le distributeur ne m'a donné que 500 AED. Je veux récupérer le reste.",
  dispute=True, reason="RC-ATM", variety="gulf")
s("disputes", "I filled up at Oasis Fuel this morning and the payment went through twice, AED 120 each.",
  "عبيت بنزين في أويسس فيول الصبح وانخصم المبلغ مرتين، 120 درهم كل مرة.",
  "J'ai fait le plein chez Oasis Fuel ce matin et le paiement est passé deux fois, 120 AED chacun.",
  dispute=True, reason="RC-DUP", variety="gulf")
s("disputes", "How do I dispute a card payment?",
  "كيف يمكنني الاعتراض على عملية دفع بالبطاقة؟",
  "Comment contester un paiement par carte ?")
s("disputes", "SkyWays Travel cancelled my flight and promised a refund of AED 1,640 a month ago. It still isn't on my card.",
  "ألغت سكاي ويز للسفر رحلتي ووعدت باسترداد 1640 درهماً قبل شهر، ولم يظهر المبلغ على بطاقتي حتى الآن.",
  "SkyWays Travel a annulé mon vol et m'a promis un remboursement de 1 640 AED il y a un mois. Toujours rien sur ma carte.",
  dispute=True, reason="RC-RFD")
s("disputes", "I paid the wrong shop by mistake. Can I get a refund?",
  "دفعت لمحل غلط بالخطأ، أقدر أسترجع فلوسي؟",
  "J'ai payé le mauvais magasin par erreur. Est-ce que je peux être remboursé ?", variety="gulf")
s("disputes", "The hotel took a AED 900 deposit on my card and never released it after I checked out. You need to chase them.",
  "الفندق حجز مبلغ تأمين 900 درهم على بطاقتي ولم يفرج عنه بعد مغادرتي. عليكم متابعتهم.",
  "L'hôtel a bloqué une caution de 900 AED sur ma carte et ne l'a jamais libérée après mon départ. Vous devez les relancer.",
  dispute=True, reason="RC-RFD")
s("disputes", "Zest Grocery charged me twice for the same shopping, 2 times AED 74.",
  "Zest Grocery 5asamou mni marratain 3ala nafs el shopping, 74 dirham marratain.",
  "Zest Grocery m'a débité deux fois pour les mêmes courses, 2 fois 74 AED.",
  dispute=True, reason="RC-DUP", variety="arabizi")
s("disputes", "Palm Fitness Club closed down a week after I paid AED 1,200 for a yearly membership, and they won't refund me.",
  "أغلق نادي بالم فيتنس بعد أسبوع من دفعي 1200 درهم لاشتراك سنوي، ويرفضون إرجاع المبلغ.",
  "Le Palm Fitness Club a fermé une semaine après que j'ai payé 1 200 AED pour un abonnement annuel, et ils refusent de me rembourser.",
  dispute=True, reason="RC-NRV")
s("disputes", "My order from Souk Online arrived broken and the seller refuses to give my money back. I paid AED 560 by card.",
  "طلبي من سوق أونلاين وصل مكسور والبائع رافض يرجع فلوسي. دفعت 560 درهم بالبطاقة.",
  "Ma commande Souk Online est arrivée cassée et le vendeur refuse de me rembourser. J'ai payé 560 AED par carte.",
  dispute=True, reason="RC-NRV", variety="gulf")

# ---------------- fraud and security (14) ----------------
s("fraud_security", "I lost my card somewhere in the mall. Please block it.",
  "فقدت بطاقتي في المول. أرجو إيقافها.",
  "J'ai perdu ma carte quelque part au centre commercial. Merci de la bloquer.", fraud=True, reason="RC-LST")
s("fraud_security", "There's a payment of AED 3,400 to an online store I've never heard of. I didn't make it!",
  "في عملية دفع بـ 3400 درهم لمتجر إلكتروني عمري ما سمعت فيه. أنا ما سويتها!",
  "Il y a un paiement de 3 400 AED à une boutique en ligne dont je n'ai jamais entendu parler. Ce n'est pas moi !",
  dispute=True, fraud=True, reason="RC-UNR", variety="gulf")
s("fraud_security", "My phone was stolen last night and it has the banking app on it.",
  "سُرق هاتفي الليلة الماضية وعليه تطبيق البنك.",
  "On m'a volé mon téléphone hier soir et l'application bancaire est dessus.", fraud=True, reason="RC-LST")
s("fraud_security", "I got an SMS saying my account is blocked and I must click a link to unblock it. Is it really from you?",
  "وصلتني رسالة تقول إن حسابي موقوف ولازم أضغط على رابط عشان أفعله. هل هي منكم فعلاً؟",
  "J'ai reçu un SMS disant que mon compte est bloqué et que je dois cliquer sur un lien. Est-ce vraiment vous ?",
  fraud=True, reason="RC-PHI", variety="gulf")
s("fraud_security", "Someone called me pretending to be from your bank and asked for my OTP. I didn't give it, but I want you to know.",
  "اتصل بي شخص يدّعي أنه من البنك وطلب رمز التحقق. لم أعطه إياه، لكنني أردت إبلاغكم.",
  "Quelqu'un m'a appelé en se faisant passer pour votre banque et m'a demandé mon code OTP. Je ne l'ai pas donné, mais je voulais vous prévenir.",
  fraud=True, reason="RC-PHI")
s("fraud_security", "A shop I used told me my card details were leaked in a data breach. Can you replace my card?",
  "أبلغني متجر تعاملت معه أن بيانات بطاقتي تسربت في اختراق للبيانات. هل يمكنكم استبدال بطاقتي؟",
  "Un magasin m'a informé que les données de ma carte avaient fuité lors d'un piratage. Pouvez-vous remplacer ma carte ?",
  fraud=True, reason="RC-LST")
s("fraud_security", "Two withdrawals from an ATM in another emirate that I never made. I was at home all day.",
  "سحبتين من صراف في إمارة ثانية وأنا ما سويتهم. كنت في البيت طول اليوم.",
  "Deux retraits dans un distributeur d'un autre émirat que je n'ai jamais faits. J'étais chez moi toute la journée.",
  dispute=True, fraud=True, reason="RC-UNR", variety="gulf")
s("fraud_security", "There's a direct debit from a company I don't know. I never signed anything, please investigate.",
  "يوجد خصم مباشر لصالح شركة لا أعرفها. لم أوقّع على أي شيء، أرجو التحقيق.",
  "Il y a un prélèvement d'une société que je ne connais pas. Je n'ai rien signé, merci d'enquêter.",
  dispute=True, fraud=True, reason="RC-UNR")
s("fraud_security", "My card got stolen, please block it now.",
  "karti msrooqa, law sama7t sakkirha alheen.",
  "On m'a volé ma carte, bloquez-la tout de suite s'il vous plaît.", fraud=True, reason="RC-LST", variety="arabizi")
s("fraud_security", "I think my account was hacked. My email and phone number were changed without me doing anything.",
  "أعتقد أن حسابي تعرض للاختراق. تم تغيير بريدي الإلكتروني ورقم هاتفي دون أن أفعل شيئاً.",
  "Je pense que mon compte a été piraté. Mon e-mail et mon numéro de téléphone ont été changés sans que je fasse quoi que ce soit.",
  fraud=True, reason="RC-LST")
s("fraud_security", "Unknown transactions on my card for three days in a row, and your hotline kept me on hold for an hour. Disgraceful.",
  "عمليات غير معروفة على بطاقتي ثلاثة أيام متتالية، وخطكم الساخن خلاني أنتظر ساعة كاملة. شي مخزي.",
  "Des transactions inconnues sur ma carte trois jours de suite, et votre service téléphonique m'a fait attendre une heure. C'est honteux.",
  dispute=True, fraud=True, reason="RC-UNR", variety="gulf")
s("fraud_security", "Forwarding an email I received asking me to 'verify my account' at ghb-secure-login.example.net. Is this real?",
  "أعيد توجيه رسالة بريد إلكتروني وصلتني تطلب مني 'التحقق من حسابي' على ghb-secure-login.example.net. هل هي حقيقية؟",
  "Je vous transfère un e-mail qui me demande de « vérifier mon compte » sur ghb-secure-login.example.net. C'est authentique ?",
  fraud=True, reason="RC-PHI")
s("fraud_security", "My wallet was stolen yesterday with both of my Gulf Horizon cards in it.",
  "انسرقت محفظتي أمس وفيها بطاقتين من بنك الأفق الخليجي.",
  "On m'a volé mon portefeuille hier avec mes deux cartes Gulf Horizon dedans.", fraud=True, reason="RC-LST", variety="gulf")
s("fraud_security", "My father has dementia and I think someone has been using his card. I'm his son. What can I do?",
  "والدي مصاب بالخرف وأعتقد أن شخصاً ما يستخدم بطاقته. أنا ابنه. ماذا يمكنني أن أفعل؟",
  "Mon père est atteint de démence et je pense que quelqu'un utilise sa carte. Je suis son fils. Que puis-je faire ?",
  fraud=True, vuln=True, reason="RC-UNR")

# ---------------- accounts and identity (12) ----------------
s("accounts_kyc", "How do I update my home address?",
  "كيف أقدر أحدث عنوان السكن؟",
  "Comment mettre à jour mon adresse ?", variety="gulf")
s("accounts_kyc", "Why do you need to verify my identity again?",
  "لماذا تحتاجون إلى التحقق من هويتي مرة أخرى؟",
  "Pourquoi devez-vous vérifier mon identité à nouveau ?")
s("accounts_kyc", "I've uploaded my Emirates ID four times and the verification keeps failing. My account is frozen and I can't pay my rent. This is unacceptable.",
  "رفعت الهوية الإماراتية أربع مرات والتحقق يفشل كل مرة. حسابي مجمد وما أقدر أدفع الإيجار. هذا شي غير مقبول.",
  "J'ai téléchargé ma carte d'identité émiratie quatre fois et la vérification échoue toujours. Mon compte est gelé et je ne peux pas payer mon loyer. C'est inacceptable.",
  complaint=True, reason="RC-ACC", variety="gulf")
s("accounts_kyc", "I would like to close my account. What do I need to do?",
  "أرغب في إغلاق حسابي. ما الإجراءات المطلوبة؟",
  "Je souhaite clôturer mon compte. Que dois-je faire ?")
s("accounts_kyc", "Close my account. Your service has been terrible for months and I'm moving to another bank.",
  "سكروا حسابي. خدمتكم سيئة من شهور وأنا بنقل لبنك ثاني.",
  "Clôturez mon compte. Votre service est déplorable depuis des mois et je pars dans une autre banque.",
  complaint=True, reason="RC-SVC", variety="gulf")
s("accounts_kyc", "I forgot my app passcode. How can I reset it?",
  "نسيت رمز الدخول للتطبيق. كيف يمكنني إعادة تعيينه؟",
  "J'ai oublié mon code d'accès à l'application. Comment le réinitialiser ?")
s("accounts_kyc", "What is the minimum age to open an account for my son?",
  "كم أقل عمر لفتح حساب لولدي؟",
  "Quel est l'âge minimum pour ouvrir un compte pour mon fils ?", variety="gulf")
s("accounts_kyc", "Can I keep my account if I move to Oman?",
  "هل يمكنني الاحتفاظ بحسابي إذا انتقلت إلى عُمان؟",
  "Puis-je garder mon compte si je déménage à Oman ?")
s("accounts_kyc", "Why are you asking for proof of my source of funds? I've been your customer for ten years. This is insulting.",
  "لماذا تطلبون إثبات مصدر أموالي؟ أنا عميل لديكم منذ عشر سنوات. هذا أمر مهين.",
  "Pourquoi me demandez-vous un justificatif de l'origine de mes fonds ? Je suis client chez vous depuis dix ans. C'est insultant.",
  complaint=True, reason="RC-ACC")
s("accounts_kyc", "How do I change the phone number registered on my account?",
  "كيف يمكنني تغيير رقم الهاتف المسجل في حسابي؟",
  "Comment changer le numéro de téléphone enregistré sur mon compte ?")
s("accounts_kyc", "I asked you to close my account three weeks ago and it's still open. Nobody replies to my emails.",
  "طلبت منكم إغلاق حسابي قبل ثلاثة أسابيع وما زال مفتوحاً. لا أحد يرد على رسائلي.",
  "Je vous ai demandé de clôturer mon compte il y a trois semaines et il est toujours ouvert. Personne ne répond à mes e-mails.",
  complaint=True, reason="RC-ACC")
s("accounts_kyc", "I can't verify my identity in the app, the photo keeps getting rejected.",
  "ma2dar a verify el hawiya fi el app, el sura kil marra tetrafa.",
  "Je n'arrive pas à vérifier mon identité dans l'application, la photo est toujours refusée.", variety="arabizi")

# ---------------- customer care: service, vulnerable customers, other (12) ----------------
s("customer_care", "The staff at your Deira branch were rude to my elderly mother today. I want to make a formal complaint.",
  "موظفو فرعكم في ديرة تعاملوا بوقاحة مع والدتي المسنة اليوم. أريد تقديم شكوى رسمية.",
  "Le personnel de votre agence de Deira a été impoli avec ma mère âgée aujourd'hui. Je souhaite déposer une réclamation officielle.",
  complaint=True, reason="RC-SVC")
s("customer_care", "My husband passed away last month. How do I close his account, and which documents do you need?",
  "توفي زوجي الشهر الماضي. كيف أغلق حسابه، وما المستندات المطلوبة؟",
  "Mon mari est décédé le mois dernier. Comment clôturer son compte et quels documents faut-il fournir ?",
  vuln=True)
s("customer_care", "I lost my job and I can't pay my credit card this month. Is there anything you can do to help?",
  "خسرت شغلي وما أقدر أدفع البطاقة الائتمانية هالشهر. تقدرون تساعدوني بأي شي؟",
  "J'ai perdu mon emploi et je ne peux pas payer ma carte de crédit ce mois-ci. Pouvez-vous m'aider ?",
  vuln=True, variety="gulf")
s("customer_care", "I'm in hospital having cancer treatment and missed one loan payment, and you charged me a late fee. Please be human about this and remove it.",
  "أنا في المستشفى أتلقى علاج السرطان وفاتني قسط واحد من القرض، فاحتسبتم علي غرامة تأخير. أرجو أن تراعوا وضعي وتلغوها.",
  "Je suis à l'hôpital pour un traitement contre le cancer et j'ai manqué une échéance de prêt, et vous m'avez facturé des pénalités de retard. Soyez humains et annulez-les.",
  complaint=True, vuln=True, reason="RC-FEE")
s("customer_care", "Your call centre hung up on me twice today. Worst service ever.",
  "مركز الاتصال عندكم سكر الخط في وجهي مرتين اليوم. أسوأ خدمة.",
  "Votre centre d'appels m'a raccroché au nez deux fois aujourd'hui. Le pire service qui soit.",
  complaint=True, reason="RC-SVC", variety="gulf")
s("customer_care", "Are any of your branches open on Saturdays?",
  "هل توجد فروع لكم تعمل يوم السبت؟",
  "Certaines de vos agences sont-elles ouvertes le samedi ?")
s("customer_care", "Your mobile app has been down all morning and I couldn't pay my bills on time.",
  "تطبيقكم معطل طوال الصباح ولم أتمكن من دفع فواتيري في موعدها.",
  "Votre application est en panne depuis ce matin et je n'ai pas pu payer mes factures à temps.",
  complaint=True, reason="RC-SVC")
s("customer_care", "I've been waiting two hours at the branch and nobody has served me.",
  "لي ساعتين أنتظر في الفرع وما حد خدمني.",
  "J'attends depuis deux heures en agence et personne ne s'est occupé de moi.",
  complaint=True, reason="RC-SVC", variety="gulf")
s("customer_care", "Thank you, the team at the Al Barsha branch were really helpful today!",
  "شكراً لكم، فريق فرع البرشاء كان متعاوناً جداً اليوم!",
  "Merci, l'équipe de l'agence d'Al Barsha a été vraiment serviable aujourd'hui !")
s("customer_care", "I'm visually impaired and your new app doesn't work with my screen reader. I can't get to my own money.",
  "أنا ضعيف البصر وتطبيقكم الجديد لا يعمل مع قارئ الشاشة. لا أستطيع الوصول إلى أموالي.",
  "Je suis malvoyant et votre nouvelle application ne fonctionne pas avec mon lecteur d'écran. Je n'ai plus accès à mon propre argent.",
  complaint=True, vuln=True, reason="RC-SVC")
s("customer_care", "I want to complain about how the branch staff treated me.",
  "abi ashtiki 3ala el mowazafeen fi el far3, ta3amlhom kan sayye2.",
  "Je veux me plaindre de la façon dont le personnel de l'agence m'a traité.",
  complaint=True, reason="RC-SVC", variety="arabizi")
s("customer_care", "I'm going through a divorce and need to split our joint account. It's a very hard time for me.",
  "أمر بإجراءات طلاق وأحتاج إلى فصل حسابنا المشترك. إنها فترة صعبة جداً بالنسبة لي.",
  "Je suis en instance de divorce et je dois séparer notre compte joint. C'est une période très difficile pour moi.",
  vuln=True)
