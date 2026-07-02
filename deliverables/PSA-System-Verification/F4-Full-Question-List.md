# F4 — Household Survey — Complete Question List

Every question the deployed app asks, in order, grouped by section — generated directly from the CSPro data dictionary so it matches the live instrument exactly. Question numbers follow the official questionnaire.

## Field Control

- **Survey Team Leader's Name**  _(text)_
- **Enumerator's Name**  _(text)_
- **Field Validated by**  _(text)_
- **Field Edited by**  _(text)_
- **Date First Visited the Household (YYYYMMDD)**  _(number)_
- **Date of Final Visit to the Household (YYYYMMDD)**  _(number)_
- **Total Number of Visits**  _(number)_
- **Result of First Visit**  _(select one)_
  - Completed · Postponed · Incomplete · Withdraw Participation/Consent
- **Result of Final Visit**  _(select one)_
  - Completed · Postponed · Incomplete · Withdraw Participation/Consent
- **Language used for the interview**  _(text)_
- **Region Code (PSGC)**  _(number)_
- **Province / HUC Code (PSGC)**  _(number)_
- **City / Municipality Code (PSGC)**  _(number)_
- **Facility Number (within municipality)**  _(number)_
- **Case Sequence (per-facility, per-instrument)**  _(number)_
- **Region (from PSGC)**  _(text)_
- **Province / HUC (from PSGC)**  _(text)_
- **City / Municipality (from PSGC)**  _(text)_

## Household Geographic Identification

- **Classification**  _(select one)_
  - UHC IS · Non-UHC IS
- **Region**  _(select one)_
  - (set at runtime)
- **Province / HUC**  _(select one)_
  - (set at runtime)
- **City / Municipality**  _(select one)_
  - (set at runtime)
- **Barangay**  _(select one)_
  - (set at runtime)
- **Household Address**  _(text)_
- **Parent F3 Patient Case Sequence**  _(number)_
- **GPS Latitude**  _(text)_
- **GPS Longitude**  _(text)_
- **GPS Altitude (m)**  _(text)_
- **GPS Accuracy (m)**  _(number)_
- **GPS Satellites**  _(number)_
- **GPS Read Time (UTC)**  _(text)_

## Case Verification Photo

- **Verification Photo Filename**  _(text)_
- **Take Verification Photo**  _(select one)_
  - Take verification photo

## A. Introduction and Informed Consent

- **1. Before we begin, to confirm, are you the household head?**  _(select one)_
  - Yes · No

## B. Respondent Profile

- **Name: (Last Name, First Name, MI, Extension)**  _(text)_
- **2. In what month were you born?**  _(number)_
- **3. What is your sex at birth?**  _(select one)_
  - Male · Female
- **4. Are you part of the LGBTQIA+ community? (e.g., gay, lesbian, bisexual, etc.). It is fine if you are not comfortable answering.**  _(select one)_
  - Yes · No · Not Comfortable to Answer · Don't Know · Refused to answer
- **5. Which group do you identify with? It is fine if you are not comfortable answering.**  _(select one)_
  - Lesbian · Gay · Bisexual · Transgender · Queer · Intersex · Asexual · Other (specify)
- **6. What is your civil status?**  _(select one)_
  - Single / Never Married · Married · Common law / Live-in · Widowed · Divorced · Separated · Annulled · Not reported
- **7. Do you identify as a person with a disability?**  _(select one)_
  - Yes · No
- **8. Would you like to specify the type of disability?**  _(select one)_
  - Yes · No
- **9. May we view your PWD Identification Card?**  _(select one)_
  - Yes (card was presented and verified) · No (card not available at the time of interview) · Respondent refused to present card
- **10. Based on the presented PWD Identification Card, what type of disability is indicated?**  _(select one)_
  - Physical disability (Orthopedic) · Visual disability · Hearing disability · Speech impairment · Intellectual disability · Psychosocial disability · Multiple disabilities · Other disability (specify)
- **11. What is the highest level of education you have attained?**  _(select one)_
  - Early Childhood Education (Pre-school) · Primary Education (Grade 1 to 6) · Lower Secondary Education (Grade 7 to 10) · Upper Secondary Education (Grade 11 to 12) · Post-Secondary Non-Tertiary Education (including Technical and Vocational degrees with a certificate) · Short-Cycle Tertiary Education or Equivalent (including Technical and Vocational degrees with a diploma) · Bachelor Level Education or Equivalent · Master Level Education or Equivalent · Doctoral Level Education or Equivalent · No schooling · Other (specify) · I don't know · Not applicable
- **12. What is your employment status?**  _(select one)_
  - Has a permanent job/ own business · Has a short-term, seasonal, casual job/business · Worked on different jobs day to day per week · Unemployed and looking for work · Unemployed and not looking for work · Retired · I don't know · Not applicable
- **13. What is your main source of income?**  _(select one)_
  - Working for private company · Working for private household · Working for government · Worked with pay in own family business or farm · Self-employed without any paid employee · Employer in own family business · Worked without pay in own family business or farm · Pension · Unemployed and looking for work · Unemployed and not looking for work · I don't know
- **14. Are you a member of Indigenous People (IP) community, like the Igorot, Lumad, Mangyans, etc.?**  _(select one)_
  - Yes · No
- **15. If yes, which group?**  _(text)_
- **16. Is your household a beneficiary of the Pantawid Pamilyang Pilipino Program (4Ps)?**  _(select one)_
  - Yes · No
- **17. Who takes the most responsibility for making the decisions regarding healthcare in your household?**  _(select one)_
  - Me (respondent) · My father · My mother · My parents · My spouse/partner · My spouse/partner and I · My sibling · My grandfather · My grandmother · My uncle · My aunt · Other (specify)
- **18. In the past 6 months, what is your average monthly household income? Approximate amount (Philippine pesos).**  _(number)_
- **19. How many total individuals (including children) live in your house now?**  _(number)_
- **20. How many non-working age children (i.e., below the age of 18) live in your house now?**  _(number)_
- **21. How many senior citizens live in your house now?**  _(number)_
- **22. Do you have electricity in your household?**  _(select one)_
  - Yes · No
- **23. What is the family's main source of water supply for daily use?**  _(select one)_
  - Faucet inside the house · Tubed/piped well · Dug well · Other (specify)
- **24. Do you have your own faucet, or do you share with your community?**  _(select one)_
  - I/we have our own · I/we share with our community
- **25. Do you have your own tube/pipe, or do you share with your community?**  _(select one)_
  - I/we have our own · I/we share with our community
- **26. Does the family own a refrigerator/freezer?**  _(select one)_
  - Yes, I/ we have · No, I/we don't have
- **27. Does the family own a television set?**  _(select one)_
  - Yes, I/ we have · No, I/we don't have
- **28. Does the family own a washing machine?**  _(select one)_
  - Yes, I/ we have · No, I/we don't have
- **29. How would the socioeconomic class of your household be classified?**  _(select one)_
  - Class A or B (working professionals or with a business with several assets) · Class C (working professionals with permanent or semi-permanent income and some assets) · Class D or E (semi-permanent workers or informal sector workers with little to no assets) · I don't know

## C. Household Roster and Characteristics

- **Household Member Line Number**  _(number)_
- **30. Name (LAST NAME, FIRST NAME & MIDDLE NAME, EXT)**  _(text)_
- **31. HH member present or away**  _(select one)_
  - Away · Present
- **32. Age (as of last birthday)**  _(number)_
- **33. Sex at birth**  _(select one)_
  - Male · Female
- **34. Relationship to Household Head**  _(select one)_
  - Head · Spouse/Partner · Son/Daughter · Brother/Sister · Son-In-Law/Daughter-In-Law · Grandson/Granddaughter · Father/Mother · Nephew/Niece · Cousin · Boarder · Domestic Helper · Non-relative
- **35. Do you identify as a person with a disability?**  _(select one)_
  - No · Yes
- **36. Would you like to specify the type of disability?**  _(select one)_
  - No · Yes
- **37. May we view the patient's PWD Identification Card?**  _(select one)_
  - No · Yes · Respondent refused to present card
- **38. Based on the presented PWD Identification Card, what type of disability is indicated?**  _(select one)_
  - Physical disability (Orthopedic) · Visual disability · Hearing disability · Speech impairment · Intellectual disability · Psychosocial disability · Multiple disabilities · Other disability (specify)
- **39. Civil Status**  _(select one)_
  - Single / Never Married · Married · Common law / Live-in · Widowed · Divorced · Separated · Annulled · Not reported
- **40. Highest level of education completed**  _(select one)_
  - Early Childhood Education (Pre-school) · Primary Education (Grade 1 to 6) · Lower Secondary Education (Grade 7 to 10) · Upper Secondary Education (Grade 11 to 12) · Post-Secondary Non-Tertiary Education (including Technical and Vocational degrees with a certificate) · Short-Cycle Tertiary Education or Equivalent (including Technical and Vocational degrees with a diploma) · Bachelor Level Education or Equivalent · Master Level Education or Equivalent · Doctoral Level Education or Equivalent · No schooling
- **41. Employment Status**  _(select one)_
  - Has a permanent job/ own business · Has a short-term, seasonal, casual job/business · Worked on different jobs day to day per week · Unemployed and looking for work · Unemployed and not looking for work · Retired · I don't know · Not applicable
- **42. Is (NAME) covered by GSIS either as a member or dependent?**  _(select one)_
  - Yes · No · I don't know
- **43. Is (NAME) covered by SSS either as a member or dependent?**  _(select one)_
  - Yes · No · I don't know
- **44. Is (NAME) covered by Pag-ibig either as a member or dependent?**  _(select one)_
  - Yes · No · I don't know
- **45. Currently registered with PhilHealth?**  _(select one)_
  - Yes · No · I don't know
- **46. What is his/her membership category? (Only answer if 'Yes' in Q45)**  _(select one)_
  - Formal economy · Informal economy · Indigent · Sponsored · Lifetime member · Senior citizen · Overseas Filipino Worker (OFW) · Qualified dependents · Dependent · Other (Specify) · I don't know
- **48. Name (First Name Only)**  _(text)_
- **49. Is (NAME) covered by a private health insurance either as a member or dependent? (Example: Maxicare, Intellicare, Pacific Cross Health Care)**  _(select one)_
  - Yes · No · I don't know
- **50. Others (Specify)**  _(text)_

## C. Household Private Insurance Gate (Q47)

- **47. Do you or other members of your HH have private insurance?**  _(select one)_
  - Yes · No

## D. Awareness on Universal Health Care (UHC)

- **51. Have you heard about Universal Health Care (UHC) prior to this survey?**  _(select one)_
  - Yes · No
- **52. What is your source of information about UHC?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **53. What is your understanding about UHC?**  _(select all that apply)_
  - Protection from financial risk/decreased out-of-pocket spending · Access to quality and affordable health care goods and services · Automatic enrollment into PhilHealth · Primary care provider for every Filipino · I don't know · Other (Specify)

## E. YAKAP/Konsulta Awareness

- **54. Have you heard of the term "YAKAP/Konsulta package"?**  _(select one)_
  - Yes · No
- **55. What are your sources of information about the YAKAP/Konsulta package?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **56. What is your understanding about the YAKAP/Konsulta package?**  _(select all that apply)_
  - Free primary care consultation (with a registered YAKAP/Konsulta provider) · Free health risk screening and assessment (with a registered YAKAP/Konsulta provider) · Free selected laboratory / diagnostics examination · Free selected drugs and medicines · There are no benefits in the package · I don't know · Other (Specify)

## F. Bagong Urgent Care and Ambulatory Service (BUCAS) Awareness and Utilization

- **57. Have you heard about Bagong Urgent Care and Ambulatory Service (BUCAS) center?**  _(select one)_
  - Yes · No
- **58. If yes, what are your sources of information about this BUCAS center?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **59. What is your understanding about a BUCAS center?**  _(select all that apply)_
  - Provides urgent care for non-life-threatening/serious conditions · Offers outpatient and ambulatory health services · Helps reduce overcrowding in hospitals · Allows access to timely medical consultation and treatment · Other (specify)
- **60. In the last six months, did you or any member of your HH accessed the services in a BUCAS center?**  _(select one)_
  - Yes · No
- **61. If yes, which of the services did you avail?**  _(select all that apply)_
  - Medical consultation for urgent or minor conditions · Outpatient or ambulatory care services · Basic diagnostic services (e.g., laboratory tests, X-ray) · Minor procedures or treatments · Referral to higher-level health facilities · I don't know · Other (specify)

## G. Access to Medicines

- **62. How often do you purchase or receive medicines?**  _(select one)_
  - Weekly · Bi-weekly · Monthly · Rarely · Never
- **63. Was the most recent medicine purchased prescribed by a doctor or over-the-counter (OTC) medicine (no need for a prescription)?**  _(select one)_
  - Prescribed by a doctor · Over-the-counter medicine · Purchased both prescribed medicine and OTC medicine · I don't know
- **64. What are the medications that you or any member of your household usually take? (List all medicines taken for the health condition.)**  _(text)_
- **65. What are the medical conditions that you/your household member/s take the medicine/s for?**  _(select all that apply)_
  - Upper respiratory infection · Hypertension · Immunization · Pregnancy or birth · Flu · Fever · Joint and muscle pain · Asthma or COPD (chronic breathing problem, not cancer) · Diabetes · Heart problem · Kidney problem / Dialysis · Cancer (any) · Gastro problem (vomiting, diarrhea, etc.) · Other infection (e.g. urine, skin, other virus etc.) · Accident/injury (e.g. wound/broken bone) · Dental · ENT (problem with ear/nose/throat) · Allergy · No condition - Regular check-up only · Other (Specify)
- **66. Where do you usually buy or receive your medicines?**  _(select all that apply)_
  - Public Hospital · Private Hospital · Chain Pharmacies (e.g. Mercury Drug, Watsons, TGP, Generika) · Local pharmacies · Online stores (e.g. Shopee, Lazada) · Barangay Health Station · Rural Health Unit or City Health Office · Other (specify)
- **67. How much time does it take for you to reach the nearest pharmacy from your home? (HHMM)**  _(number)_
- **68. How easy is it for you to access a pharmacy or drugstore?**  _(select one)_
  - Very difficult · Difficult · Neutral · Easy · Very easy
- **69. Have you heard of the Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT) Package, which is part of PhilHealth's YAKAP/Konsulta or primary care benefit package?**  _(select one)_
  - Yes · No
- **70. If yes, what are your sources of information for GAMOT Package?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **71. What is your understanding of the GAMOT Package?**  _(select all that apply)_
  - Provides free or affordable medicines for outpatients · Ensures continuous availability of essential medicines · Helps reduce out-of-pocket expenses for medicines · Supports treatment of common illnesses and chronic conditions · I don't know · Other (specify)
- **72. Did you get the medicines from the GAMOT Package during the past 6 months?**  _(select one)_
  - Yes · No
- **73. What are the medications that you obtained from the GAMOT Package? [LIST]**  _(text)_
- **74. Where did you get the rest of the medicines?**  _(select all that apply)_
  - Purchased from pharmacy · Purchased from public hospital · Purchased from private hospital · Purchased from primary care provider (PCP) · Received from PCP for free · Received from LGU for free · Received from public hospital for free · Received from private hospital for free · Not applicable · Other (Specify)
- **75. Do you know the difference between a 'branded' and a 'generic' medicine?**  _(select one)_
  - Yes · No
- **76. Was/were the medicine/s you bought outside of GAMOT pharmacy branded or generic?**  _(select one)_
  - Branded · Generic · Both branded and generic · Don't know the difference · Not applicable
- **77. If generic, why did you buy generic medicine?**  _(select all that apply)_
  - Lower cost · Prescribed by doctor · Readily available · Given for free · More or as effective as branded medicine · I don't know · Not applicable · Other (Specify)
- **78. If branded, why did you buy branded medicine? (Ask if answer in Q76 is branded and both branded and generic, otherwise skip.)**  _(select all that apply)_
  - Branded medicine is more effective than generic · Not aware of generic option · Prescribed by doctor · Given for free · Prefer branded over generic option · I don't know · Not applicable · Other (Specify)

## H. PhilHealth Registration and Health Insurance

- **79. How did you find out about how to register to PhilHealth?**  _(select one)_
  - PhilHealth representative · LGU · Primary care provider · Other health care provider · Employer · No one / self-registered · Barangay Health Worker · Friends / Family · Health center/facility · Other (Specify)
- **80. Who assisted you in the registration process?**  _(select one)_
  - PhilHealth representative · LGU · Primary care provider · Other health care provider · Employer · No one / self-registered · Barangay Health Worker · Friends / Family · Health center/facility · Other (Specify)
- **81. Did you have any difficulties in the registration process?**  _(select one)_
  - Yes · No
- **82. What did you find difficult about the process?**  _(select all that apply)_
  - Unclear process · Took a long time · Did not know where to ask for help · Had to travel a long way · No valid ID · Did not know the required documents to register · I don't know · Other (Specify)
- **83. Would you know where to go to seek assistance in registration?**  _(select one)_
  - Yes · No
- **84. Where would you go to seek assistance?**  _(text)_
- **85. What are some of the benefits that come with being a PhilHealth member?**  _(select all that apply)_
  - No balance billing for basic ward accommodation · Subsidized inpatient services · Subsidized outpatient services · There are no benefits to being a member · I don't know · Other (Specify)
- **86. Do you and members of your HH pay PhilHealth premiums every month?**  _(select one)_
  - Yes, I pay directly · Yes, my employer pays · No, I do not pay premiums
- **87. Do you find it difficult to pay the PhilHealth premiums every month?**  _(select one)_
  - Yes · No
- **88. Why did you find it difficult?**  _(select all that apply)_
  - Cannot afford the premium · Payment options are inconvenient · No time to pay · Don't see value in paying · System of PhilHealth is unreliable/usually down · I don't know · Other (Specify)

## I. Primary Care Utilization

- **89. In the past 12 months, do you have a clinic, or health center that you usually go to?**  _(select one)_
  - Yes · No · I don't know
- **90. Is this the facility you usually go to for general health concerns?**  _(select one)_
  - Yes · No
- **91. Why did you go to this facility?**  _(select all that apply)_
  - This facility is more accessible than my usual facility (i.e., nearer, has more transportation options to get to, and cheaper to travel to) · Needed a service/specialist not available at my usual facility · Recommended by friends/family · Wanted to try another facility than my usual · Prefer this facility than my usual · This was referred to me by my usual facility · Usual facility is closed for today · The doctor I trust/familiar with transferred in this facility · Other (Specify)
- **92. What is the type of facility that you usually go to?**  _(select one)_
  - YAKAP/Konsulta or primary care provider · Barangay Health Center · Rural Health Unit / Health Center · Public Hospital · Private Hospital · Private Clinic · Traditional Healer or Manghihilot/Albularyo · I don't know · Other (Specify)
- **93. If not, why do you not have a usual clinic, or health center that you usually go to?**  _(select all that apply)_
  - I don't get sick · I recently moved into the area · It's expensive · I can treat myself · I don't know where to go for care · I don't know · Other (Specify)
- **94. What mode/s of transportation do you use when travelling to the nearest primary care facility?**  _(select all that apply)_
  - Walk · Bike · Public Bus · Jeepney · Tricycle · Car (including private taxi/cab) · Motorcycle · Boat · Taxi · Pedicab · E-bike · Other (Specify)
- **95. How long does it take you to travel from your house when going to the nearest primary care facility? (one-way, minutes)**  _(number)_
- **96. How much does it usually cost for you to travel to this facility from your home? (PHP, one-way)**  _(number)_
- **97. When you have a health problem, do you know how to book an appointment at a primary care facility?**  _(select one)_
  - Yes · No
- **98. When your primary care facility is open, can you get advice quickly over the phone if you need it?**  _(select one)_
  - Yes · No · I haven't tried · I don't know
- **99. When your primary care facility is closed, is there a phone number you can call when you get sick?**  _(select one)_
  - Yes · No · I haven't tried · I don't know
- **100. When you have to visit your primary care facility, do you have to take a leave from work or school to go?**  _(select one)_
  - Yes · No · I haven't tried · I don't know · Not applicable

## J. Household Members' Health-Seeking Behavior and Outcomes

- **101. How often do you/your household member have a general check-up on your health (i.e., when you feel healthy, without any specific illness)?**  _(select one)_
  - More than once a year · Every year · Every 2-3 years · Every 4-5 years · No set time; I've only ever done this once or twice in my life · Never; I only go to the doctor when I am sick · Other (Specify)
- **102. What best describes why you/your household member will visit a health facility (e.g. RHU, health center, clinic, hospital)?**  _(select all that apply)_
  - Consultation for new health problem · Consultation to follow-up an ongoing health problem · For tests/diagnostics only · For a general check-up · To get a health certificate/administrative reason · For immunizations/vaccinations · My doctor transferred to this health facility · Other (Specify)
- **103. Have you accessed any of the following forms of care in the last 6 months?**  _(select all that apply)_
  - Outpatient care (Consultation, procedure, or treatment where the patient visits and leaves within the same day) · Inpatient care (Care provided in hospital or another facility where the patient is admitted for at least one night) · Emergency care (Care for serious illnesses or injuries that need immediate medical attention; usually provided in an emergency room or ER) · Primary care consultation · Other (Specify)
- **104. Have you ever consulted a physician for preventative reasons, such as to consult about your lifestyle, weight loss, stopping smoking, etc.?**  _(select one)_
  - Yes · No
- **105. In the last 6 months, have you or any of your household members had a medical problem and chosen NOT to see a healthcare provider?**  _(select one)_
  - Yes · No
- **106. Why not?**  _(select all that apply)_
  - Not sick enough · It's too expensive · Could not take time off work · Could not get an appointment soon enough · No transportation available · Afraid to know my illness · I don't know · Other (Specify)
- **107. Did you or your household members do any other actions to improve your/their health condition or address your/their health concern?**  _(select all that apply)_
  - Visited other healthcare facility · Sought alternative care (Healthcare apart from medical doctors or the formal healthcare system; such as... · Sought telemedicine (Remote diagnosis and treatment of patients by means of telecommunications technology) · Used home care (Healthcare services and support provided to individuals in their own homes) · Bought medicine from a pharmacy · Did not seek other forms of care · Other (Specify)

## K. Experiences and Satisfaction with Referrals

- **108. In the past 6 months, did a healthcare worker refer you to another facility or specialist for further care or specialized care?**  _(select one)_
  - Yes · No
- **109. What type of care was the referral for?**  _(select all that apply)_
  - Outpatient care (Consultation, procedure, or treatment where the patient visits and leaves within the same day) · Emergency care (Care for serious illnesses or injuries that need immediate medical attention; usually provided in an emergency room or ER) · Inpatient care (Care provided in hospital or another facility where the patient is admitted for at least one night) · Dental care (Medical care for your teeth, such as cleanings, fillings, etc.) · Other facility visits (Care that is provided in a facility that is not a health center or hospital, such as independent diagnostic centers, TB dispensaries, etc.) · Special therapy visits (Rehabilitation care or services, such as occupational therapy, physical therapy, psychological and behavioral rehabilitation, prosthetics and orthotics rehabilitation, or speech... · Alternative care (Healthcare apart from medical doctors or the formal health care system; such as reflexology, acupuncture, massage therapy, herbal medicines, etc.) · Outreach / medical missions (Care provided by the government or an NGO through an outreach or medical mission within a community) · Home healthcare (Care that is administered at the patient's home, such as birth delivery, checkups, immunization, rehabilitation, etc.) · Telemedicine (Remote diagnosis and treatment of patients by means of telecommunications technology) · None of the above · Other (Specify)
- **110. What kind of specialist did they recommend?**  _(select one)_
  - No specialty · Anesthesia · Dermatology · Emergency Medicine · Family Medicine · General Surgery · Internal Medicine · Neurology · Nuclear Medicine · Obstetrics and Gynecology · Occupational Medicine · Ophthalmology · Orthopedics · Otorhinolaryngology (ENT) · Pathology · Pediatrics · Physical and Rehabilitation Medicine · Psychiatry · Public health · Radiology · Research · I don't know · Other (Specify)
- **111. How did they refer you to the doctor?**  _(select one)_
  - Physical referral slip · E-referral · Phone call from referring facility to receiving facility · I don't know · Other (Specify)
- **112. Did you visit another facility after the referral?**  _(select one)_
  - Yes · No, I'm not planning to · Not yet, but I'm planning to
- **113. Why are you not planning to visit?**  _(select all that apply)_
  - Facility is too far · Do not trust the referred facility · No time · Worried about additional costs · Not needed · Don't know how to get to facility · Other (Specify)
- **114. Did they discuss with you the different places you could have gone to get help with your problem?**  _(select one)_
  - Yes · No
- **115. Did they help you make the appointment for that visit?**  _(select one)_
  - Yes · No
- **116. Did they write down any information for the specialist about the reason for that visit?**  _(select one)_
  - Yes · No
- **117. After you went to the specialist or special service, did they follow up with you about what happened at the visit? (Only if Q112=Yes)**  _(select one)_
  - Yes · No
- **118. Overall, how would you rate your satisfaction with the referral process? (Only if Q112=Yes)**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable
- **119. Was the visit to the facility a referral from your primary care facility?**  _(select one)_
  - Yes · No
- **120. Does your primary care provider know that you made the visit?**  _(select one)_
  - Yes · No · I don't know
- **121. As it was not a referral, why did you decide to visit a hospital?**  _(select all that apply)_
  - Referred by other specialist (doctor in another hospital) · Nearest facility to house · Facility is usual source of care · Facility is the only place that can perform a certain test · Referred by BHW/nurse/midwife/other community health professional · Referred by family / friends · Facility offers subsidized or free health services · I don't know · Other (Specify)
- **122. Did your primary care provider discuss with you different places you could have gone to get help with your problem?**  _(select one)_
  - Yes · No
- **123. Did your primary care provider (PCP) or someone working with your PCP help you make the appointment for that visit?**  _(select one)_
  - Yes · No
- **124. Did your primary care provider write down any information for the specialist about the reason for that visit?**  _(select one)_
  - Yes · No
- **125. Overall, how would you rate your experience with the referral process?**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable

## L. No Balance Billing (NBB) Awareness and Utilization

- **126. Have you heard of the No Balance Billing (NBB)?**  _(select one)_
  - Yes · No · I don't know
- **127. If yes, what are your sources of information about NBB?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **128. What is your understanding about NBB?**  _(select all that apply)_
  - Patient does not pay any hospital bill · Bills are settled between the hospital and PhilHealth · PhilHealth will cover cost of treatment · Patients should not be charged extra fees · Medicine and service are already included · I don't know · No cash payment required upon discharge · Other (Specify) · Applies only to certain patients or hospitals
- **129. Were you or any of your household members confined in a hospital during the past 6 months?**  _(select one)_
  - Yes · No · I don't know
- **130. For the most recent hospitalization, what type of hospital?**  _(select one)_
  - Public · DOH-retained hospital (sub-type of public hospital) · Private
- **131. During your hospitalization in a DOH-retained hospital, did you or your family pay anything out-of-pocket before being discharged that should have been covered under NBB?**  _(select one)_
  - Yes · No · I don't know

## M. Zero Balance Billing (ZBB) Awareness + MAIFIP + Bill Breakdown

- **132. Have you heard of the Zero Balance Billing (ZBB)?**  _(select one)_
  - Yes · No · I don't know
- **133. If yes, what are your sources of information about ZBB?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **134. What is your understanding about ZBB?**  _(select all that apply)_
  - Patient does not pay any hospital bill · Bills are settled between the hospital and PhilHealth · PhilHealth will cover cost of treatment · Patients should not be charged extra fees · Medicine and service are already included · I don't know · No cash payment required upon discharge · Other (Specify) · Applies only to certain patients or hospitals
- **135. During your hospitalization in a DOH-retained hospital, did you or your family pay anything out-of-pocket before being discharged that should have been covered under ZBB?**  _(select one)_
  - Yes · No · I don't know
- **136. Have you heard of the Medical Assistance for Indigent and Financially Incapacitated Patients (MAIFIP)?**  _(select one)_
  - Yes · No · I don't know
- **137. What are your sources of information about MAIFIP?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **138. From your most recent visit, which among the charges was the most expensive?**  _(select one)_
  - Medicine · Laboratory Tests · Medical Supplies · Doctor's Fee
- **139. From your most recent visit, what was the final amount you paid in cash at the hospital cashier upon discharge? (PHP)**  _(number)_
- **140. From your most recent visit, do you recall the breakdown of the bill?**  _(select one)_
  - Yes · No
- **141. From your most recent visit, which of the following were included in the bill?**  _(select all that apply)_
  - Rooms <for inpatients only> · Doctor's Fee · Diagnostic or laboratory procedure · Medical equipment or supplies · Medicines or drugs · Non-medical expenses (e.g. hygiene kit) · Other expenses
- **142. From your most recent visit, do you recall how you paid for your bill?**  _(select one)_
  - Yes · No
- **143. From your most recent visit, how did you pay?**  _(select all that apply)_
  - Own income/ household income · PhilHealth · Private insurance / HMO · Loan · Sale of assets · Donations from charities / NGOs · Donations from LGUs / LGU programs · National Government Agencies (DSWD, etc.) · Paid by someone else · Other (Specify)

## N. Household Expenditures (WHO/SHA)

- **144. Cereals (rice, flour, noodles, corn, etc.)**  _(select one)_
  - Yes · No
- **145. Pulses, roots, tubers, plantains, (and cooking bananas), and nuts**  _(select one)_
  - Yes · No
- **146. Vegetables (fresh, dried, dehydrated, frozen)**  _(select one)_
  - Yes · No
- **147. Fruits in any form (fresh, dried, dehydrated, frozen)**  _(select one)_
  - Yes · No
- **148. Fish and other seafoods in any form (fresh, dried, dehydrated, frozen)**  _(select one)_
  - Yes · No
- **149. Any kind of meat and offal in any form (fresh, dried, dehydrated, frozen)**  _(select one)_
  - Yes · No
- **150. Any kind of egg (from chicken, duck, quail, etc.)**  _(select one)_
  - Yes · No
- **151. Milk and other milk products, excluding butter**  _(select one)_
  - Yes · No
- **152. Butter, lard, other animal-based oils and fats, and vegetable oils (coconut, palm, sesame)**  _(select one)_
  - Yes · No
- **153. Sugar, jaggery and other sugar confectionary and desserts (including nut pastes)**  _(select one)_
  - Yes · No
- **154. Condiments and other spices and other ready-made meals**  _(select one)_
  - Yes · No
- **155. Water and non-alcoholic beverages (e.g., coffee)**  _(select one)_
  - Yes · No
- **156. Alcoholic beverages (e.g., local and imported)**  _(select one)_
  - Yes · No
- **157. Sub-total (food, last week)**  _(number)_
- **158. Meals and snacks and beverages from restaurants (dine-in, take-out, and deliveries)**  _(select one)_
  - Yes · No
- **159. Smoking (e.g., cigarettes, cigars, and vape), and/or smokeless tobacco products (e.g., chewing tobacco, betel nut)**  _(select one)_
  - Yes · No
- **160. Personal care products (e.g., shampoo, haircut)**  _(select one)_
  - Yes · No
- **161. Household cleaning and maintenance products and services including domestic ones**  _(select one)_
  - Yes · No
- **162. Utilities like electricity, water supply, refuse and sewage collection, and fuels (including gas)**  _(select one)_
  - Yes · No
- **163. Passenger transportation services (jeepney, bus, train, taxi, plane, school bus) including rentals and online purchases and fuels and lubricants for personal vehicle**  _(select one)_
  - Yes · No
- **164. Telephone line and mobile phone services, WIFI access, cable TV and any other communication and audio services including repairs and installations**  _(select one)_
  - Yes · No
- **165. Recreational, cultural, religious, sporting and entertainment devices (monthly)**  _(select one)_
  - Yes · No
- **166. Postal services**  _(select one)_
  - Yes · No
- **167. Housing (actual rentals, estimated value of rent if owned)**  _(select one)_
  - Yes · No
- **168. Recreational, cultural, religious, sporting and entertainment devices (6-month)**  _(select one)_
  - Yes · No
- **169. Ready-made clothing, fabric and materials for clothing, and footwear including household textile, glassware, table ware and household utensils including repairs**  _(select one)_
  - Yes · No
- **170. Educational services (e.g., tuitions and tutoring)**  _(select one)_
  - Yes · No
- **171. Accommodation services, including for educational establishment (e.g., hotels)**  _(select one)_
  - Yes · No
- **172. Garden and personal pets' products and services**  _(select one)_
  - Yes · No
- **173. Health insurance**  _(select one)_
  - Yes · No
- **174. Other insurance (e.g., for life and accident, and travel)**  _(select one)_
  - Yes · No
- **175. Inpatient care services**  _(select one)_
  - Yes · No
- **176. Emergency transportation and emergency rescue services**  _(select one)_
  - Yes · No
- **177. Total value of 175 and 176 (health, 12-month)**  _(number)_
- **178. Preventive services such as immunization/vaccinations services and other preventive services (e.g., tetanus toxoid for pregnant women, and routine immunization such as BCG during well child visits). Exclude the cost of vaccine itself.**  _(select one)_
  - Yes · No
- **179. Diagnostic and laboratory tests, such as blood tests and x-rays, for other reasons than preventive care**  _(select one)_
  - Yes · No
- **180. Assistive health products for vision (e.g., glasses), hearing (e.g., hearing aids), and mobility (e.g., crutches, therapeutic footwear), including repair, rental, and online purchases**  _(select one)_
  - Yes · No
- **181. Medical products (e.g., antigen tests, glucose meters, masks), including online purchases**  _(select one)_
  - Yes · No
- **182. Total value of 178 to 181 (health, 6-month)**  _(number)_
- **183. Medicines (branded, generic, herbal), vaccines, oral contraceptives, and other pharmaceutical preparations, including online purchases**  _(select one)_
  - Yes · No
- **184. Outpatient medical and dental services, including online services, without overnight stay**  _(select one)_
  - Yes · No
- **185. Total value of 183 and 184 (health, 1-month)**  _(number)_

## O. Sources of Funds for Health

- **186. Current income of any household members**  _(select one)_
  - Yes · No
- **187. Savings, pension**  _(select one)_
  - Yes · No
- **188. Selling of any household's assets or goods (housing, land, animals, jewelry, appliances, or machines)**  _(select one)_
  - Yes · No
- **189. Borrowing from friends or relatives outside the household**  _(select one)_
  - Yes · No
- **190. Borrowing from institutions (e.g., financial, microfinance arrangements)**  _(select one)_
  - Yes · No
- **191. Remittance or money gift**  _(select one)_
  - Yes · No
- **192. Government assistance (DSWD, local, etc.)**  _(select one)_
  - Yes · No
- **193. Donation from LGUs**  _(select one)_
  - Yes · No
- **194. Other specify**  _(select one)_
  - Yes · No
- **195. What portion of your household's monthly income would you be willing to set aside for health care if it reduced unexpected medical expenses?**  _(select one)_
  - None · Less than 1% · 1-3% · 4-6% · More than 6% · Don't know
- **196. If your household chooses not to spend on health care for financial reasons, what kind of care do you usually forego?**  _(select all that apply)_
  - Doctor/consultation visit · Medicines or treatments · Laboratory tests / diagnostics · Hospital admission / inpatient care · Preventive care (e.g., vaccinations, check-ups) · Dental care · Other (please specify) · We do not forego care

## P. Financial Risk Protection: Incidence of Reduced/Delayed Care

- **197. In the last 6 months, have you or your household member delayed seeking care for financial reasons?**  _(select one)_
  - Yes · No
- **198. In the last 6 months, have you or your household member seen a doctor and not fully followed their advice (for example, to buy prescribed medicine, to go for a follow-up consultation, to get additional diagnostics) for financial reasons?**  _(select one)_
  - Yes · No
- **199. The usual price for a consultation ranges from Php 500 to Php 2,000. What is the highest amount you are willing to pay for a consultation?**  _(select one)_
  - Php 0 – Php 249 · Php 250 – Php 499 · Php 500 – Php 999 · Php 1,000 – Php 1249 · Php 1,250 – Php 1499 · Php 1,500 – Php 1749 · Php 1,750 – Php 1999 · Php 2,000 and above · Other (Specify)

## Q. Anxiety about Household Finances

- **200. Have you or your household had to reduce spending on things you need (such as food, housing, or utilities) because of this health expenditure in the last 1 month?**  _(select one)_
  - Yes · No · Don't know · Refused to answer
- **201. How worried are you about your household's finances in the next 1 month?**  _(select one)_
  - Very worried · Somewhat worried · Not too worried · Not worried at all
- **202. Do any of the following reasons describe why you are worried about your household's finances in the next 1 month?**  _(select all that apply)_
  - Loss of income · Healthcare costs related to coronavirus (COVID-19) · Healthcare costs NOT related to coronavirus (COVID-19) (including to treat other diseases, illnesses, injuries, or symptoms)

*Total: 237 questions/fields across the instrument.*
