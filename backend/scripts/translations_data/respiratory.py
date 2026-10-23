"""Translations for Acute Respiratory Infections, Acute Rhinosinusitis, and Sore Throat / Pharyngitis."""

RESPIRATORY_TRANSLATIONS: dict[str, tuple[str, str]] = {
    # === acute_respiratory_infections ===
    "Breathing rate above 30 breaths per minute": (
        "प्रति मिनट 30 से अधिक बार सांस लेना",
        "दर मिनिटास 30 पेक्षा जास्त वेळा श्वास घेणे",
    ),
    "Blue or purple colour on the lips, fingertips, or face (cyanosis), indicates critically low oxygen": (
        "होंठ, उंगलियों के पोर या चेहरे का नीला या बैंगनी पड़ना (सायनोसिस), जो ऑक्सीजन के अत्यंत कम स्तर का संकेत है",
        "ओठ, बोटांची टोके किंवा चेहऱ्यावर निळसर किंवा जांभळा रंग येणे (सायनोसिस), जे अत्यंत कमी ऑक्सिजनचे लक्षण आहे",
    ),
    "Oxygen saturation at or below 92% in a person aged 50 or below, or below 90% in a person over 50": (
        "50 वर्ष या उससे कम उम्र के व्यक्ति में ऑक्सीजन का स्तर 92% या उससे कम, या 50 वर्ष से अधिक उम्र में 90% से कम होना",
        "50 किंवा त्यापेक्षा कमी वयाच्या व्यक्तीमध्ये ऑक्सिजनचे प्रमाण 92% किंवा त्याहून कमी, किंवा 50 वर्षांपेक्षा जास्त वयाच्या व्यक्तीमध्ये 90% पेक्षा कमी असणे",
    ),
    "Oxygen saturation at or below 92%": (
        "ऑक्सीजन का स्तर 92% या उससे कम होना",
        "ऑक्सिजन पातळी 92% किंवा त्याहून कमी असणे",
    ),
    "Confusion or disorientation along with breathing problems": (
        "सांस की समस्या के साथ भ्रम या अचेतनता होना",
        "श्वासाच्या त्रासासोबत गोंधळलेली मानसिक अवस्था किंवा असंबद्धता असणे",
    ),
    "Very low blood pressure combined with breathing difficulty": (
        "सांस लेने में कठिनाई के साथ बहुत कम रक्तचाप (लो BP)",
        "श्वास घेण्यास त्रास आणि सोबत अतिशय कमी रक्तदाब (लो BP)",
    ),
    "Chest pain that worsens with breathing or coughing": (
        "सीने में दर्द जो सांस लेने या खांसने पर बढ़ जाता है",
        "छातीत दुखणे जे श्वास घेताना किंवा खोकताना अधिक वाढते",
    ),
    "Coughing up blood (frank haemoptysis), may also suggest TB or a more serious condition": (
        "खांसी में खून आना (हेमोप्टाइसिस), जो टीबी या किसी अन्य गंभीर बीमारी का संकेत हो सकता है",
        "खोकल्यातून रक्त पडणे, जे टीबी किंवा इतर गंभीर आजाराचे लक्षण असू शकते",
    ),
    "Cough or cold with wheezing (whistling sound in chest)": (
        "खांसी या जुकाम के साथ सीने से सीटी जैसी आवाज (घरघराहट) आना",
        "खोकला किंवा सर्दीसोबत छातीतून शिट्टीसारखा आवाज (घरघर) येणे",
    ),
    "Suspected pneumonia in a person aged 65 or above, or with confusion, low blood pressure, or fast breathing": (
        "65 वर्ष या उससे अधिक उम्र के व्यक्ति में, या भ्रम, कम रक्तचाप, या तेज सांस के साथ संदिग्ध निमोनिया",
        "65 वर्षे किंवा त्याहून अधिक वयाच्या व्यक्तीमध्ये, किंवा गोंधळ, कमी रक्तदाब किंवा जलद श्वासोच्छ्वासासह संशयित न्यूमोनिया",
    ),
    "Any respiratory illness in a person with diabetes, heart disease, chronic lung disease, or kidney disease, these are high-risk groups": (
        "मधुमेह, हृदय रोग, फेफड़ों की पुरानी बीमारी या गुर्दे के रोग से पीड़ित व्यक्ति में कोई भी श्वसन रोग, ये उच्च जोखिम वाले समूह हैं",
        "मधुमेह, हृदयरोग, फुफ्फुसाचा जुनाट आजार किंवा मूत्रपिंडाचा आजार असलेल्या व्यक्तीमध्ये श्वसनाचा आजार, हे उच्च जोखीम गट आहेत",
    ),
    "Suspected flu with breathing difficulty, especially if there is a history of recent travel or an ongoing flu epidemic": (
        "सांस लेने में कठिनाई के साथ संदिग्ध फ्लू, विशेषकर यदि हाल की यात्रा का इतिहास हो या फ्लू फैला हो",
        "श्वासाच्या त्रासासह संशयित फ्लू, विशेषतः अलीकडील प्रवासाचा इतिहास असल्यास किंवा फ्लूची साथ असल्यास",
    ),
    "Rest and stay home away from others to avoid spreading the infection": (
        "संक्रमण फैलने से रोकने के लिए आराम करें और दूसरों से दूर घर पर रहें",
        "संसर्ग पसरू नये म्हणून विश्रांती घ्या आणि इतरांपासून सुरक्षित अंतर ठेवून घरी राहा",
    ),
    "Drink plenty of fluids, water, warm soups, warm water with honey and ginger, coconut water": (
        "प्रचुर मात्रा में तरल पदार्थ पिएं, जैसे पानी, गर्म सूप, शहद और अदरक के साथ गुनगुना पानी, नारियल पानी",
        "पुरेसे द्रवपदार्थ प्या, जसे पाणी, गरम सूप, मध आणि आल्यासह कोमट पाणी, नारळ पाणी",
    ),
    "Steam inhalation can help relieve nasal and chest congestion": (
        "भाप लेने से नाक और सीने की जकड़न से राहत मिल सकती है",
        "वाफ घेतल्याने नाक आणि छातीतील कफ किंवा दाटणे मोकळे होण्यास मदत होते",
    ),
    "Warm salt water gargling helps relieve throat discomfort": (
        "गुनगुने नमक के पानी से गरारे करने से गले की तकलीफ में आराम मिलता है",
        "कोमट मिठाच्या पाण्याच्या गुळण्या केल्याने घशातील खवखव आणि त्रास कमी होतो",
    ),
    "Paracetamol can be taken for fever or body aches as per the dosage on the pack": (
        "बुखार या बदन दर्द के लिए पैकेज पर दिए गए निर्देशानुसार पैरासिटामोल लिया जा सकता है",
        "ताप किंवा अंगदुखीसाठी पॅकवरील सूचनेनुसार पॅरासिटामॉल घेता येऊ शकते",
    ),
    "Avoid smoking and exposure to smoke or dust": (
        "धूम्रपान से बचें और धुएं या धूल के संपर्क में न आएं",
        "धूम्रपान टाळा आणि धूर किंवा धुळीच्या संपर्कात येणे टाळा",
    ),
    "Viral upper respiratory infections (common cold) do not benefit from antibiotics, do not self-medicate with antibiotics": (
        "वायरल ऊपरी श्वसन संक्रमण (सामान्य सर्दी) में एंटीबायोटिक्स से कोई लाभ नहीं होता, खुद से एंटीबायोटिक्स न लें",
        "व्हायरल वरच्या श्वसनमार्गाच्या संसर्गात (सामान्य सर्दी) अँटीबायोटिक्सचा फायदा होत नाही, स्वतःहून अँटीबायोटिक्स घेऊ नका",
    ),
    "Cough lasting more than 10 to 14 days without improvement": (
        "बिना किसी सुधार के 10 से 14 दिन से अधिक समय तक चलने वाली खांसी",
        "कोणत्याही सुधाराशिवाय 10 ते 14 दिवसांपेक्षा जास्त काळ टिकणारा खोकला",
    ),
    "Cough producing yellow, green, or blood-tinged sputum": (
        "पीला, हरा या खून के अंश वाला बलगम आने वाली खांसी",
        "पिवळा, हिरवा किंवा रक्ताची छटा असणारा कफ पडणारा खोकला",
    ),
    "No improvement after 2 to 3 days of treatment for bronchitis or a prescribed antibiotic course": (
        "ब्रोंकाइटिस के 2 से 3 दिन के उपचार या निर्धारित एंटीबायोटिक कोर्स के बाद भी सुधार न होना",
        "ब्राँकायटिसच्या 2 ते 3 दिवसांच्या उपचारानंतर किंवा दिलेल्या अँटीबायोटिक कोर्सनंतरही सुधारणा न होणे",
    ),
    "Symptoms that started improving but then got significantly worse": (
        "लक्षण जो पहले सुधरने लगे थे लेकिन फिर अचानक काफी बिगड़ गए",
        "लक्षणे जी आधी सुधारत होती पण नंतर अचानक खूपच बिघडली",
    ),
    "Any danger sign listed above, breathing rate above 30, blue lips, inability to speak, confusion, coughing blood": (
        "ऊपर सूचीबद्ध कोई भी खतरे का संकेत, सांस की दर 30 से ऊपर, नीले होंठ, बोलने में असमर्थता, भ्रम, खांसी में खून आना",
        "वर नमूद केलेले धोक्याचे कोणतेही लक्षण, श्वासाचा वेग 30 पेक्षा जास्त, निळे ओठ, बोलता न येणे, गोंधळ, खोकल्यातून रक्त येणे",
    ),
    "Most mild colds and coughs in a healthy adult resolve within 7 to 10 days without medication": (
        "स्वस्थ वयस्क में अधिकांश हल्की सर्दी और खांसी बिना दवा के 7 से 10 दिन के भीतर ठीक हो जाती है",
        "निरोगी प्रौढ व्यक्तीमध्ये बहुतांश हलकी सर्दी आणि खोकला औषधांशिवाय 7 ते 10 दिवसांत बरा होतो",
    ),
    "Acute Upper Respiratory Infection (common cold, catarrh)": (
        "एक्यूट अपर रेस्पिरेटरी इन्फेक्शन (सामान्य सर्दी, जुकाम)",
        "तीव्र वरच्या श्वसनमार्गाचा संसर्ग (सामान्य सर्दी, पडसे)",
    ),
    "Acute Bronchitis": (
        "एक्यूट ब्रोंकाइटिस (श्वसन नली की सूजन)",
        "तीव्र ब्राँकायटिस (श्वासनलिका दाह)",
    ),
    "Community Acquired Pneumonia (CAP)": (
        "कम्युनिटी एक्वायर्ड निमोनिया (सीएपी)",
        "कम्युनिटी अक्वायर्ड न्यूमोनिया (सीएपी)",
    ),

    # === acute_rhinosinusitis ===
    "Severe headache with stiff neck, may indicate meningitis": (
        "गर्दन में अकड़न के साथ तेज सिरदर्द, जो मेनिन्जाइटिस (दिमागी बुखार) का संकेत हो सकता है",
        "मानेच्या ताठरतेसह तीव्र डोकेदुखी, जे मेंदूज्वराचे (मेनिंजायटिस) लक्षण असू शकते",
    ),
    "Swelling or redness around the eye, or eye being pushed forward (proptosis), indicates the infection has spread to the eye socket": (
        "आंख के चारों ओर सूजन या लालिमा, या आंख का आगे की ओर उभरना (प्रॉप्टोसिस), जो संक्रमण के आंख के गड्ढे में फैलने का संकेत है",
        "डोळ्याभोवती सूज किंवा लालसरपणा, किंवा डोळा पुढे ढकलला जाणे, जे संसर्ग डोळ्याच्या खोबणीत पसरल्याचे दर्शवते",
    ),
    "Double vision or significant vision disturbance": (
        "दोहरी दृष्टि (एक का दो दिखना) या दृष्टि में गंभीर गड़बड़ी",
        "दुहेरी दृष्टी (एकाचे दोन दिसणे) किंवा दृष्टीमध्ये लक्षणीय बिघाड",
    ),
    "Increasing swelling or fullness on the forehead": (
        "माथे पर लगातार बढ़ती सूजन या भारीपन",
        "कपाळावर वाढणारी सूज किंवा कपाळ भरून आल्यासारखे वाटणे",
    ),
    "Altered mental state or confusion, indicates the infection may have spread to the brain": (
        "मानसिक स्थिति में बदलाव या भ्रम, जो संक्रमण के मस्तिष्क में फैलने का संकेत हो सकता है",
        "बदललेली मानसिक स्थिती किंवा गोंधळ, जे संसर्ग मेंदूपर्यंत पसरल्याचे दर्शवू शकते",
    ),
    "Facial skin, palate, or inner nasal tissues turning dark or discoloured, suggests invasive fungal sinusitis, which is a medical emergency, especially in diabetic patients": (
        "चेहरे की त्वचा, तालू या नाक के अंदर के ऊतकों का काला या रंगहीन पड़ना, जो इनवेसिव फंगल साइनसाइटिस का संकेत है, विशेषकर मधुमेह रोगियों में यह एक मेडिकल इमरजेंसी है",
        "चेहऱ्याची त्वचा, टाळू किंवा नाकातील आतील ऊती काळ्या पडणे, जे बुरशीजन्य संसर्गाचे (फंगल सायनुसायटिस) लक्षण आहे, विशेषतः मधुमेही रुग्णांमध्ये ही वैद्यकीय आणीबाणी आहे",
    ),
    "Drink adequate fluids to keep mucus thin and easier to drain": (
        "बलगम को पतला रखने और आसानी से बाहर निकालने के लिए पर्याप्त तरल पदार्थ पिएं",
        "कफ पातळ ठेवण्यासाठी आणि सहज बाहेर पडण्यासाठी पुरेसे द्रवपदार्थ प्या",
    ),
    "Steam inhalation for 10 to 15 minutes, two or three sessions a day, can relieve nasal congestion": (
        "दिन में 2 या 3 बार, 10 से 15 मिनट के लिए भाप लेने से नाक की जकड़न दूर हो सकती है",
        "दिवसातून 2 किंवा 3 वेळा, 10 ते 15 मिनिटे वाफ घेतल्याने नाकातील चोंदणे कमी होऊ शकते",
    ),
    "Rinse the nose with normal saline nasal wash, dissolve a pinch of salt in a cup of clean water and gently rinse each nostril. This helps clear mucus and improves breathing": (
        "सामान्य सलाइन नेजल वॉश से नाक साफ करें, एक कप साफ पानी में एक चुटकी नमक घोलें और धीरे से प्रत्येक नथुने को धोएं। इससे बलगम साफ होता है और सांस लेना आसान होता है",
        "सलाईनच्या पाण्याने नाक स्वच्छ धुवा, एका कप स्वच्छ पाण्यात चिमूटभर मीठ विरघळवा आणि दोन्ही नाकपुड्या हळुवार धुवा. यामुळे कफ मोकळा होतो आणि श्वास घेणे सुलभ होते",
    ),
    "Sleep with your head slightly elevated to help drainage": (
        "बलगम के निकास में मदद के लिए सिर को थोड़ा ऊंचा रखकर सोएं",
        "कफ सहजरीत्या बाहेर पडावा यासाठी डोके थोडे उंचावर ठेवून झोपा",
    ),
    "Avoid smoking and exposure to tobacco smoke, dust, and strong chemical smells": (
        "धूम्रपान से बचें और तंबाकू के धुएं, धूल और तेज रासायनिक गंध के संपर्क से दूर रहें",
        "धूम्रपान टाळा आणि तंबाखूचा धूर, धूळ आणि तीव्र रासायनिक वासापासून दूर राहा",
    ),
    "Do not use nasal decongestant sprays for more than 3 to 5 days, prolonged use can worsen nasal congestion": (
        "नाक खोलने वाले स्प्रे (नेजल डिकंजेस्टेंट) का उपयोग 3 से 5 दिन से अधिक न करें, लंबे समय तक उपयोग से नाक की जकड़न और बिगड़ सकती है",
        "नाक मोकळे करणारे स्प्रे 3 ते 5 दिवसांपेक्षा जास्त वापरू नका, दीर्घकाळ वापरामुळे नाकातील चोंदणे अधिक वाढू शकते",
    ),
    "Nasal blockage, nasal discharge, or facial pressure or pain lasting more than 7 days after a cold": (
        "सर्दी के बाद 7 दिन से अधिक समय तक नाक बंद रहना, नाक बहना, या चेहरे पर दबाव या दर्द रहना",
        "सर्दीनंतर 7 दिवसांपेक्षा जास्त काळ नाक बंद राहणे, नाकातून पाणी वाहणे, किंवा चेहऱ्यावर दाब किंवा वेदना होणे",
    ),
    "Pain or pressure over the cheeks, forehead, or between the eyes": (
        "गालों, माथे या आँखों के बीच में दर्द या दबाव महसूस होना",
        "गाल, कपाळ किंवा डोळ्यांच्या मध्ये वेदना किंवा दाब जाणवणे",
    ),
    "Thick yellow or green nasal discharge with fever": (
        "बुखार के साथ गाढ़ा पीला या हरा नाक का स्राव होना",
        "तापासह नाकातून घट्ट पिवळा किंवा हिरवट स्राव येणे",
    ),
    "Reduced or absent sense of smell": (
        "सूंघने की क्षमता कम होना या पूरी तरह समाप्त होना",
        "वास घेण्याची क्षमता कमी होणे किंवा नष्ट होणे",
    ),
    "Facial numbness or reduced sensation on the face": (
        "चेहरे का सुन्न होना या चेहरे पर संवेदना कम होना",
        "चेहरा बधीर होणे किंवा चेहऱ्यावरील संवेदना कमी होणे",
    ),
    "Recurrent sinusitis episodes (more than once in a few months)": (
        "बार-बार साइनसाइटिस होना (कुछ महीनों में 1 से अधिक बार)",
        "वारंवार सायनुसायटिसचा त्रास होणे (काही महिन्यांत 1 पेक्षा जास्त वेळा)",
    ),
    "Symptoms not improving after a full course of prescribed antibiotics": (
        "निर्धारित एंटीबायोटिक्स का पूरा कोर्स करने के बाद भी लक्षणों में सुधार न होना",
        "दिलेल्या अँटीबायोटिक्सचा पूर्ण कोर्स संपल्यानंतरही लक्षणांमध्ये सुधारणा न होणे",
    ),
    "Address dental hygiene, untreated upper tooth decay can cause sinus infection on that side": (
        "दांतों की स्वच्छता पर ध्यान दें, ऊपरी दांत की अनुपचारित सड़न उस तरफ साइनस संक्रमण का कारण बन सकती है",
        "दातांच्या आरोग्याची काळजी घ्या, वरच्या दातातील कीड त्या बाजूला सायनस संसर्गास कारणीभूत ठरू शकते",
    ),
    "Sinusitis in a person with diabetes, they must see a doctor promptly given higher risk of severe infection": (
        "मधुमेह से पीड़ित व्यक्ति में साइनसाइटिस, गंभीर संक्रमण के उच्च जोखिम को देखते हुए उन्हें तुरंत डॉक्टर से मिलना चाहिए",
        "मधुमेह असलेल्या व्यक्तीमध्ये सायनुसायटिस, गंभीर संसर्गाचा धोका जास्त असल्याने त्वरित डॉक्टरांचा सल्ला घेतला पाहिजे",
    ),
    "Signs of sinusitis in a person with diabetes or on immunosuppressive treatment, these individuals are at high risk of a rapidly worsening infection": (
        "मधुमेह या इम्यूनोसप्रेसिव उपचार ले रहे व्यक्ति में साइनसाइटिस के लक्षण, इनमें संक्रमण के तेजी से बिगड़ने का उच्च जोखिम होता है",
        "मधुमेह किंवा प्रतिकारशक्ती कमी करणाऱ्या उपचारांवर असलेल्या व्यक्तीमध्ये सायनुसायटिसची लक्षणे, संसर्ग वेगाने बळावण्याचा मोठा धोका असतो",
    ),
    "Sinusitis with suspected dental origin, pain on one side of the face near upper teeth": (
        "दांतों से जुड़ा संदिग्ध साइनसाइटिस, चेहरे के एक तरफ ऊपरी दांतों के पास दर्द होना",
        "दातांशी संबंधित संशयित सायनुसायटिस, वरच्या दातानजीक चेहऱ्याच्या एका बाजूला वेदना होणे",
    ),
    "Any red flag sign listed above, eye swelling, double vision, confusion, stiff neck, forehead fullness, dark facial tissue": (
        "ऊपर सूचीबद्ध कोई भी गंभीर लक्षण, आंख में सूजन, दोहरी दृष्टि, भ्रम, गर्दन में अकड़न, माथे पर भारीपन, चेहरे के काले पड़ते ऊतक",
        "वर नमूद केलेले कोणतेही धोक्याचे लक्षण, डोळ्याला सूज, दुहेरी दृष्टी, गोंधळ, मान ताठरणे, कपाळावर सूज, चेहऱ्यावरील काळी पडलेली त्वचा",
    ),
    "Suspected invasive fungal sinusitis in a diabetic or immunocompromised person": (
        "मधुमेह या कमजोर प्रतिरक्षा वाले व्यक्ति में संदिग्ध इनवेसिव फंगल साइनसाइटिस",
        "मधुमेही किंवा कमी प्रतिकारशक्ती असलेल्या व्यक्तीमध्ये संशयित इनवेसिव्ह फंगल सायनुसायटिस",
    ),
    "Worsening symptoms while already on antibiotic treatment": (
        "एंटीबायोटिक उपचार पर होने के बावजूद लक्षणों का और बिगड़ना",
        "अँटीबायोटिक उपचार सुरू असतानाही लक्षणे अधिक बिघडणे",
    ),
    "No improvement after 10 days of correctly prescribed antibiotic treatment": (
        "उचित रूप से निर्धारित एंटीबायोटिक उपचार के 10 दिन बाद भी कोई सुधार न होना",
        "योग्य प्रकारे दिलेल्या अँटीबायोटिक उपचारानंतर 10 दिवसांनीही कोणतीही सुधारणा न होणे",
    ),
    "Symptoms lasting less than 7 days after a cold are usually viral and self-limiting, rest, fluids, and saline nasal wash are appropriate": (
        "सर्दी के बाद 7 दिन से कम समय तक रहने वाले लक्षण आमतौर पर वायरल होते हैं और अपने आप ठीक हो जाते हैं, आराम, तरल पदार्थ और सलाइन नेजल वॉश उपयुक्त हैं",
        "सर्दीनंतर 7 दिवसांपेक्षा कमी काळ टिकणारी लक्षणे सहसा व्हायरल असतात आणि आपोआप बरी होतात, विश्रांती, पुरेसे पाणी आणि सलाईनचा वापर योग्य आहे",
    ),
    "Sinusitis is suspected when nasal blockage, nasal discharge, or facial pain lasting more than 7 days follows a cold. Symptoms lasting less than 7 days are usually a viral cold and do not need antibiotics.": (
        "सर्दी के बाद 7 दिन से अधिक समय तक नाक बंद रहना, नाक बहना या चेहरे पर दर्द रहना साइनसाइटिस का संकेत है। 7 दिन से कम समय तक रहने वाले लक्षण सामान्यतः वायरल सर्दी होते हैं और इनमें एंटीबायोटिक्स की आवश्यकता नहीं होती।",
        "सर्दीनंतर 7 दिवसांपेक्षा जास्त काळ नाक बंद राहणे, स्राव वाहणे किंवा चेहऱ्यात दुखणे म्हणजे सायनुसायटिसचा संशय असतो. 7 दिवसांपेक्षा कमी काळ टिकणारी लक्षणे सामान्यतः सर्दी असतात आणि त्यासाठी अँटीबायोटिक्सची गरज नसते.",
    ),

    # === pharyngitis_sore_throat ===
    "Sore throat with high fever, drooling of saliva, and difficulty or inability to swallow, this may indicate epiglottitis or a deep neck infection, which can close the airway": (
        "तेज बुखार के साथ गले में खराश, लार टपकना, और निगलने में कठिनाई या असमर्थता, यह एपिग्लोटाइटिस या गर्दन के गहरे संक्रमण का संकेत हो सकता है, जो सांस नली को बंद कर सकता है",
        "तीव्र तापासह घशात खवखव, तोंडून लाळ गळणे आणि गिळताना प्रचंड त्रास किंवा गिळता न येणे, हे एपिग्लोटायटिस किंवा मानेतील गंभीर संसर्गाचे लक्षण असू शकते, ज्यामुळे श्वासनलिका बंद होऊ शकते",
    ),
    "Breathing difficulty or noisy breathing with a sore throat": (
        "गले में खराश के साथ सांस लेने में कठिनाई या सांस लेते समय आवाज आना",
        "घशात खवखव असताना श्वास घेण्यास त्रास होणे किंवा घरघर असा आवाज येणे",
    ),
    "Inability to open the mouth (trismus) with sore throat, may indicate a peritonsillar abscess": (
        "गले में खराश के साथ मुंह खोलने में असमर्थता (ट्रिसमस), जो पेरिटॉन्सिलर फोड़े का संकेत हो सकता है",
        "घसा दुखण्यासोबत तोंड उघडण्यास असमर्थता (जबडा आवळणे), जे टॉन्सिलभोवती पू झाल्याचे (अ‍ॅब्सेस) लक्षण असू शकते",
    ),
    "One tonsil significantly larger than the other, especially with severe throat pain and fever, may be a peritonsillar abscess": (
        "एक टॉन्सिल का दूसरे की तुलना में काफी बड़ा होना, विशेषकर तेज गले के दर्द और बुखार के साथ, यह पेरिटॉन्सिलर फोड़ा हो सकता है",
        "एक टॉन्सिल दुसऱ्यापेक्षा लक्षणीयरीत्या मोठा असणे, विशेषतः तीव्र घसादुखी आणि तापासह, हे टॉन्सिलमधील पूचे लक्षण असू शकते",
    ),
    "Muffled or hot potato voice (very thick, muffled speech) with sore throat": (
        "गले में खराश के साथ भारी या दबी हुई आवाज (गर्म आलू जैसी आवाज)",
        "घसा दुखण्यासोबत तोंडात गरम बटाटा धरल्यासारखा अस्पष्ट आणि जड आवाज येणे",
    ),
    "White or grey membrane in the throat that extends beyond the tonsils with a very unwell appearance, may be diphtheria": (
        "गले में सफेद या भूरी झिल्ली जो टॉन्सिल से आगे फैली हो और मरीज बहुत अस्वस्थ दिखे, यह डिप्थीरिया (गलघोंटू) हो सकता है",
        "घशात टॉन्सिलच्या पुढे पसरलेली पांढरी किंवा राखाडी पडदा (झिल्ली) आणि अत्यंत अस्वस्थ वाटणे, हा घटसर्प (डिप्थीरिया) असू शकतो",
    ),
    "Swelling of the throat visible from outside the neck": (
        "गर्दन के बाहर से दिखाई देने वाली गले की सूजन",
        "मानेच्या बाहेरून स्पष्ट दिसणारी घशाची सूज",
    ),
    "Gargle with warm salt water several times a day, dissolve half a teaspoon of salt in a glass of warm water and gargle for 30 seconds. This reduces swelling and kills surface bacteria": (
        "दिन में कई बार गुनगुने नमक के पानी से गरारे करें, एक गिलास गर्म पानी में आधा चम्मच नमक घोलें और 30 सेकंड तक गरारे करें। यह सूजन कम करता है और सतह के बैक्टीरिया को मारता है",
        "दिवसातून अनेक वेळा कोमट मिठाच्या पाण्याच्या गुळण्या करा, एका ग्लास कोमट पाण्यात अर्धा चमचा मीठ विरघळवा आणि 30 सेकंद गुळण्या करा. यामुळे सूज कमी होते आणि जंतूंचा नाश होतो",
    ),
    "Drink warm liquids: warm water, warm water with honey and ginger, warm soups, warm herbal teas": (
        "गर्म तरल पदार्थ पिएं: गुनगुना पानी, शहद और अदरक के साथ गर्म पानी, गर्म सूप, गर्म हर्बल चाय",
        "गरम पातळ पदार्थ प्या: कोमट पाणी, मध आणि आल्यासह गरम पाणी, गरम सूप, काढा किंवा हर्बल चहा",
    ),
    "Rest your voice and avoid shouting or excessive talking": (
        "अपनी आवाज को आराम दें और चिल्लाने या अत्यधिक बात करने से बचें",
        "आवाजाला विश्रांती द्या, ओरडणे किंवा जास्त बोलणे टाळा",
    ),
    "Avoid smoking and exposure to tobacco smoke, smoke irritates the throat and slows healing": (
        "धूम्रपान और तंबाकू के धुएं से बचें, धुआं गले में जलन पैदा करता है और ठीक होने की प्रक्रिया धीमी करता है",
        "धूम्रपान आणि तंबाखूचा धूर टाळा, धुरामुळे घशात जळजळ होते आणि बरे होण्यास विलंब होतो",
    ),
    "Paracetamol or ibuprofen can be taken for pain relief as directed on the pack": (
        "दर्द से राहत के लिए पैकेज पर दिए गए निर्देशानुसार पैरासिटामोल या इबुप्रोफेन लिया जा सकता है",
        "वेदना कमी करण्यासाठी पॅकवरील सूचनेनुसार पॅरासिटामॉल किंवा आयबुप्रोफेन घेता येऊ शकते",
    ),
    "Avoid very cold drinks and ice cream if they worsen the pain": (
        "यदि बहुत ठंडे पेय और आइसक्रीम से दर्द बढ़ता है तो इनसे बचें",
        "अतिशय थंड पेये आणि आईस्क्रीममुळे वेदना वाढत असल्यास ते टाळा",
    ),
    "Address GERD (acid reflux) if it is a known issue, acid coming back up is a common cause of throat irritation": (
        "यदि एसिड रिफ्लक्स (जीईआरडी) की समस्या है तो उसका ध्यान रखें, पेट का एसिड ऊपर आना गले में जलन का एक सामान्य कारण है",
        "अ‍ॅसिडिटी किंवा छातीत जळजळ (जीईआरडी) असल्यास काळजी घ्या, वर येणारे अ‍ॅसिड घशातील खवखवीचे सामान्य कारण आहे",
    ),
    "Do not demand or self-purchase antibiotics for a sore throat, most sore throats are viral and antibiotics will not help": (
        "गले की खराश के लिए एंटीबायोटिक्स की मांग न करें या खुद न खरीदें, अधिकांश गले की खराश वायरल होती है और एंटीबायोटिक्स से फायदा नहीं होगा",
        "घसादुखीसाठी अँटीबायोटिक्सचा हट्ट करू नका किंवा स्वतः विकत घेऊ नका, बहुतांश घसादुखी व्हायरल असते आणि अँटीबायोटिक्सने फरक पडत नाही",
    ),
    "Sore throat that is not improving after 5 to 7 days of home care": (
        "घर पर देखभाल के 5 से 7 दिन बाद भी गले की खराश में सुधार न होना",
        "घरी काळजी घेऊनही 5 ते 7 दिवसांनंतर घशातील खवखव किंवा वेदना कमी न होणे",
    ),
    "Sore throat with high fever (above 38.5 degrees Celsius) and swollen, tender glands in the neck": (
        "तेज बुखार (38.5 degrees Celsius से अधिक) और गर्दन में सूजी हुई दर्दनाक ग्रंथियों के साथ गले में खराश",
        "तीव्र ताप (38.5 degrees Celsius पेक्षा जास्त) आणि मानेमध्ये सुजलेल्या, दुखऱ्या ग्रंथींसह घसादुखी",
    ),
    "Pus or white spots visible on the tonsils": (
        "टॉन्सिल पर मवाद या सफेद धब्बे दिखाई देना",
        "टॉन्सिल्सवर पू किंवा पांढरे डाग दिसणे",
    ),
    "Throat pain that is severe enough to make swallowing very difficult": (
        "गले में इतना तेज दर्द होना जिससे कुछ भी निगलना बहुत कठिन हो जाए",
        "घशात इतक्या तीव्र वेदना होणे ज्यामुळे गिळणे अत्यंत कठीण होते",
    ),
    "Sore throat with runny nose, cough, and red eyes, likely a viral infection but should be assessed if it is severe": (
        "बहती नाक, खांसी और लाल आँखों के साथ गले में खराश, यह संभवतः वायरल संक्रमण है लेकिन गंभीर होने पर जांच करानी चाहिए",
        "नाक वाहणे, खोकला आणि डोळे लाल होण्यासह घसादुखी, हा बहुधा व्हायरल संसर्ग असू शकतो पण त्रास जास्त असल्यास तपासणी करावी",
    ),
    "Sore throat in a person with a history of rheumatic fever or rheumatic heart disease, streptococcal throat infection can trigger a relapse": (
        "रुमेटिक फीवर या रुमेटिक हृदय रोग के इतिहास वाले व्यक्ति में गले में खराश, स्ट्रेप्टोकोकल संक्रमण इसे दोबारा भड़का सकता है",
        "रुमॅटिक ताप किंवा रुमॅटिक हृदयरोग झालेल्या व्यक्तीमध्ये घसादुखी, अशा संसर्गामुळे आजार पुन्हा उद्भवू शकतो",
    ),
    "Sore throat with generalised swollen glands across the body (neck, armpits, groin) and feeling very unwell": (
        "पूरे शरीर (गर्दन, कांख, कमर) में सूजी हुई ग्रंथियों और अत्यधिक अस्वस्थता के साथ गले में खराश",
        "संपूर्ण शरीरात (मान, काखा, जांघ) ग्रंथींना सूज येणे आणि अत्यंत आजारी वाटण्यासह घसादुखी",
    ),
    "Recurring sore throats or tonsillitis (more than 5 episodes a year)": (
        "बार-बार गले की खराश या टॉन्सिलाइटिस होना (वर्ष में 5 से अधिक बार)",
        "वारंवार घसा दुखणे किंवा टॉन्सिल्सचा त्रास होणे (वर्षातून 5 पेक्षा जास्त वेळा)",
    ),
    "Sore throat with ear pain": (
        "गले में खराश के साथ कान में दर्द होना",
        "घसा दुखण्यासोबत कान दुखणे",
    ),
    "Complications after a sore throat: new swelling in the neck, inability to open mouth, high fever returning after initial improvement": (
        "गले की खराश के बाद जटिलताएं: गर्दन में नई सूजन, मुंह खोलने में असमर्थता, शुरुआती सुधार के बाद फिर से तेज बुखार आना",
        "घसादुखीनंतरची गुंतागुंत: मानेवर नवीन सूज, तोंड उघडता न येणे, सुरुवातीच्या सुधारणेनंतर पुन्हा तीव्र ताप येणे",
    ),
    "Sore throat with new cardiac symptoms or joint swelling after recovery, may suggest rheumatic fever, a complication of streptococcal infection": (
        "ठीक होने के बाद दिल के नए लक्षण या जोड़ों में सूजन के साथ गले की खराश, जो रुमेटिक बुखार का संकेत हो सकता है",
        "बरे झाल्यानंतर हृदयाची नवीन लक्षणे किंवा सांध्यांना सूज येणे, जे रुमॅटिक तापाचे लक्षण असू शकते",
    ),
    "Any red flag sign listed above, drooling, breathing difficulty, muffled voice, single very swollen tonsil, throat membrane, inability to open the mouth": (
        "ऊपर सूचीबद्ध कोई भी गंभीर लक्षण, लार टपकना, सांस लेने में कठिनाई, दबी आवाज, एक टॉन्सिल में अत्यधिक सूजन, गले में झिल्ली, मुंह खोलने में असमर्थता",
        "वर नमूद केलेले कोणतेही धोक्याचे लक्षण, लाळ गळणे, श्वास घेण्यास त्रास, जड आवाज, एक टॉन्सिल खूप सुजणे, घशात पडदा, तोंड न उघडता येणे",
    ),
    "Suspected epiglottitis or deep neck space infection, these can close the airway rapidly": (
        "संदिग्ध एपिग्लोटाइटिस या गर्दन के गहरे स्थान का संक्रमण, ये सांस की नली को तेजी से बंद कर सकते हैं",
        "संशयित एपिग्लोटायटिस किंवा मानेतील खोल संसर्ग, यामुळे श्वासनलिका वेगाने बंद होऊ शकते",
    ),
    "Suspected diphtheria in a child who is unvaccinated or incompletely vaccinated": (
        "अप्रतिरक्षित या आंशिक रूप से प्रतिरक्षित बच्चे में संदिग्ध डिप्थीरिया",
        "लसीकरण न झालेल्या किंवा अपूर्ण लसीकरण झालेल्या बालकामध्ये संशयित घटसर्प (डिप्थीरिया)",
    ),
    "Most viral sore throats resolve on their own within 7 to 10 days with home care": (
        "अधिकांश वायरल गले की खराश घर पर देखभाल से 7 से 10 दिन के भीतर अपने आप ठीक हो जाती है",
        "बहुतांश व्हायरल घसादुखी घरगुती काळजीने 7 ते 10 दिवसांत आपोआप बरी होते",
    ),
    "Sore throat is pain in the throat on swallowing. It may be caused by a virus (most common) or bacteria. Viral sore throats do not need antibiotics. Bacterial sore throat (streptococcal) has specific features and needs a doctor to decide on treatment.": (
        "गले की खराश निगलने पर गले में होने वाला दर्द है। यह वायरस (सबसे आम) या बैक्टीरिया के कारण हो सकता है। वायरल गले की खराश में एंटीबायोटिक्स की आवश्यकता नहीं होती। बैक्टीरियल खराश के विशिष्ट लक्षण होते हैं और उपचार का निर्णय डॉक्टर को करना चाहिए।",
        "घसा दुखणे म्हणजे अन्न किंवा पाणी गिळताना घशात वेदना होणे. हा त्रास विषाणू (सर्वात सामान्य) किंवा जीवाणूंमुळे होऊ शकतो. व्हायरल घसादुखीसाठी अँटीबायोटिक्सची गरज नसते. जिवाणू संसर्गाची लक्षणे वेगळी असतात आणि डॉक्टर त्याचा योग्य उपचार ठरवतात.",
    ),
    "Breathing with the belly moving opposite to the chest (abdominal-thoracic paradox), a sign of severe breathing difficulty": (
        "पेट का सीने के विपरीत चलना (एब्डोमिनल-थोरैसिक पैराडॉक्स), जो सांस लेने में गंभीर कठिनाई का संकेत है",
        "श्वास घेताना पोट छातीच्या विरुद्ध दिशेने हलणे (पॅराडॉक्सिकल श्वासोच्छ्वास), जे श्वासाच्या तीव्र त्रासाचे लक्षण आहे",
    ),
    "Only able to speak a few words at a time due to breathlessness": (
        "सांस फूलने के कारण एक बार में केवल कुछ ही शब्द बोल पाना",
        "धाप लागल्यामुळे एका वेळी फक्त काहीच शब्द बोलता येणे",
    ),
    "Very high or very low body temperature alongside breathing difficulty": (
        "सांस की कठिनाई के साथ शरीर का तापमान बहुत अधिक या बहुत कम होना",
        "श्वासाच्या त्रासासोबत शरीराचे तापमान अतिशय जास्त किंवा खूप कमी असणे",
    ),
    "Avoid cold beverages and cold environments": (
        "ठंडे पेय पदार्थों और ठंडे वातावरण से बचें",
        "थंड पेये आणि थंड वातावरण टाळा",
    ),
    "Fever that is persistent, high, or accompanied by chills": (
        "बुखार जो लगातार बना रहे, तेज हो, या ठंड (कंपकंपी) के साथ आए",
        "ताप जो सतत राहतो, तीव्र आहे, किंवा थंडी वाजून येतो",
    ),
    "Significant breathlessness during light activity or at rest": (
        "हल्की गतिविधि के दौरान या आराम करते समय भी सांस फूलना",
        "किरकोळ हालचाली करताना किंवा विश्रांती घेत असतानाही धाप लागणे",
    ),
    "Sore throat with high fever and swollen neck glands": (
        "तेज बुखार और गर्दन की सूजी हुई ग्रंथियों के साथ गले में खराश",
        "तीव्र ताप आणि मानेतील सुजलेल्या ग्रंथींसह घसादुखी",
    ),
    "Cough with night sweats, unexplained weight loss, or prolonged fatigue, these may be signs of TB": (
        "रात में पसीना आना, बिना कारण वजन कम होना, या लंबे समय तक थकान के साथ खांसी, ये टीबी के संकेत हो सकते हैं",
        "रात्री घाम येणे, अकारण वजन कमी होणे, किंवा दीर्घकाळ थकवा असण्यासह खोकला, ही टीबीची (क्षयरोगाची) लक्षणे असू शकतात",
    ),
    "Suspected epidemic flu with breathing difficulty": (
        "सांस की कठिनाई के साथ संदिग्ध महामारी फ्लू",
        "श्वासाच्या त्रासासह संशयित साथीचा फ्लू",
    ),
}
