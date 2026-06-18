# F3 — Patient Survey — Complete Question List

Every question the deployed app asks, in order, grouped by section — generated directly from the CSPro data dictionary so it matches the live instrument exactly. Question numbers follow the official questionnaire.

## Field Control

- **Survey Team Leader's Name**  _(text)_
- **Enumerator's Name**  _(text)_
- **Field Validated by**  _(text)_
- **Field Edited by**  _(text)_
- **Date First Visited the Patient (YYYYMMDD)**  _(number)_
- **Date of Final Visit to the Patient (YYYYMMDD)**  _(number)_
- **Total Number of Visits**  _(number)_
- **Result of First Visit**  _(select one)_
  - Completed · Completed at the Hospital · Postponed · Incomplete · Completed at Home · Withdraw Participation/Consent
- **Result of Final Visit**  _(select one)_
  - Completed · Completed at the Hospital · Postponed · Incomplete · Completed at Home · Withdraw Participation/Consent
- **Language used for the interview**  _(text)_
- **Type of Patient**  _(select one)_
  - Outpatient · Inpatient
- **Region Code (PSGC)**  _(number)_
- **Province / HUC Code (PSGC)**  _(number)_
- **City / Municipality Code (PSGC)**  _(number)_
- **Facility Number (within municipality)**  _(number)_
- **Case Sequence (per-facility, per-instrument)**  _(number)_
- **Region (from PSGC)**  _(text)_
- **Province / HUC (from PSGC)**  _(text)_
- **City / Municipality (from PSGC)**  _(text)_

## Patient Geographic Identification

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
- **Facility Name**  _(text)_
- **Facility Address**  _(text)_
- **Patient Home Region**  _(select one)_
  - (set at runtime)
- **Patient Home Province / HUC**  _(select one)_
  - (set at runtime)
- **Patient Home City / Municipality**  _(select one)_
  - (set at runtime)
- **Patient Home Barangay**  _(select one)_
  - (set at runtime)

## Facility GPS Capture

- **GPS Latitude**  _(text)_
- **GPS Longitude**  _(text)_
- **GPS Altitude (m)**  _(text)_
- **GPS Accuracy (m)**  _(number)_
- **GPS Satellites**  _(number)_
- **GPS Read Time (UTC)**  _(text)_

## Patient Home GPS Capture

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

- **1. Before we begin, to confirm, are you the patient?**  _(select one)_
  - Yes · No
- **2. What is your relationship to the patient?**  _(select one)_
  - Spouse · Son · Daughter · Step-son · Step-daughter · Son-in-law · Daughter-in-law · Grandson · Granddaughter · Father · Mother · Brother · Sister · Uncle · Aunt · Nephew · Niece · Neighbor · Other (specify) · Refuse to answer (DO NOT READ OUT LOUD)
- **3. Do you live in the same house as the patient?**  _(select one)_
  - Yes · No

## B. Patient Profile

- **4. Patient's Name (Last Name, First Name, MI, Extension)**  _(text)_
- **5. In what month and year was the patient born?**  _(number)_
- **6. Just to confirm, how old is the patient as of his/her last birthday? (in years)**  _(number)_
- **7. What is the patient's sex at birth?**  _(select one)_
  - Male · Female
- **8. Is the patient part of the LGBTQIA+ community? (e.g., gay, lesbian, bisexual, etc.). It is fine if not comfortable answering.**  _(select one)_
  - Yes · No · Not Comfortable to Answer · Don't Know · Refused to answer
- **9. Which group does the patient identify with?**  _(select one)_
  - Lesbian · Gay · Bisexual · Transgender · Queer · Intersex · Asexual · Other (specify)
- **10. What is the patient's civil status?**  _(select one)_
  - Single / Never Married · Married · Common law / Live-in · Widowed · Divorced · Separated · Annulled · Not reported
- **11. Does the patient identify as a person with a disability?**  _(select one)_
  - Yes · No
- **12. Would the patient like to specify the type of disability?**  _(select one)_
  - Yes · No
- **13. May we view the patient's PWD Identification Card?**  _(select one)_
  - Yes (card was presented and verified) · No (card not available at the time of interview) · Respondent refused to present card
- **14. Based on the presented PWD Identification Card, what type of disability is indicated?**  _(select one)_
  - Physical disability (Orthopedic) · Visual disability · Hearing disability · Speech impairment · Intellectual disability · Psychosocial disability · Multiple disabilities · Other disability (specify)
- **15. What is the highest level of education the patient has attained?**  _(select one)_
  - Early Childhood Education (Pre-school) · Primary Education (Grade 1 to 6) · Lower Secondary Education (Grade 7 to 10) · Upper Secondary Education (Grade 11 to 12) · Post-Secondary Non-Tertiary Education (including Technical and Vocational degrees with a certificate) · Short-Cycle Tertiary Education or Equivalent (including Technical and Vocational degrees with a diploma) · Bachelor Level Education or Equivalent · Master Level Education or Equivalent · Doctoral Level Education or Equivalent · No schooling · Other (specify) · I don't know · Not applicable
- **16. What is the patient's employment status?**  _(select one)_
  - Has a permanent job/ own business · Has a short-term, seasonal, casual job/business · Worked on different jobs day to day per week · Unemployed and looking for work · Unemployed and not looking for work · Studying · Retired · I don't know · Not applicable
- **17. What is the patient's main source of income?**  _(select one)_
  - Working for private company · Working for private household · Working for government · Worked with pay in own family business or farm · Self-employed without any paid employee · Worked without pay in own family business or farm · Pension · Unemployed and looking for work · Unemployed and not looking for work · I don't know
- **18. In the past 6 months, what is the patient's average monthly household income? Please specify in Philippine pesos.**  _(number)_
- **19. How many total individuals (including children) live in the patient's house now?**  _(number)_
- **20. How many non-working age children (i.e., below the age of 18) live in the patient's house now?**  _(number)_
- **21. How many senior citizens live in the patient's house now?**  _(number)_
- **22. Does the patient have electricity in their household?**  _(select one)_
  - Yes · No
- **23. What is the patient's family's main source of water supply for daily use?**  _(select one)_
  - Faucet inside the house · Tubed/piped well · Dug well · Other (specify)
- **24. Does the patient have their own faucet, or do they share with their community?**  _(select one)_
  - I/we have our own · I/we share with our community
- **25. Does the patient have their own tube/pipe, or do they share with their community?**  _(select one)_
  - I/we have our own · I/we share with our community
- **26. Does the patient's family own a refrigerator/freezer?**  _(select one)_
  - Yes, I/ we have · No, I/we don't have
- **27. Does the patient's family own a television set?**  _(select one)_
  - Yes, I/ we have · No, I/we don't have
- **28. Does the patient's family own a washing machine?**  _(select one)_
  - Yes, I/ we have · No, I/we don't have
- **29. How would the socioeconomic class of the patient's household be classified?**  _(select one)_
  - Class A or B (working professionals or with a business with several assets) · Class C (working professionals with permanent or semi-permanent income and some assets) · Class D or E (semi-permanent workers or informal sector workers with little to no assets) · I don't know
- **30. Is the patient member of Indigenous People (IP) community, like the Igorot, Lumad, Mangyans, etc.?**  _(select one)_
  - Yes · No
- **31. If yes, which group? (Specify)**  _(text)_
- **32. Is the patient's household a beneficiary of the Pantawid Pamilyang Pilipino Program (4Ps)?**  _(select one)_
  - Yes · No
- **33. Is the patient the main decision-maker on health care in your household?**  _(select one)_
  - Yes (the Patient is the main decision maker) · No · The Companion answering the survey is the main decision maker
- **34. Who takes the most responsibility for making the decisions regarding healthcare in the patient's household?**  _(select one)_
  - Patient's father · Patient's mother · Patient's parents · Patient's spouse/partner · Both patient and spouse · Patient's sibling · Patient's grandfather · Patient's grandmother · Patient's uncle · Patient's aunt · Other (specify)

## C. Awareness on Universal Health Care (UHC)

- **35. Have you heard about Universal Health Care (UHC) prior to this survey?**  _(select one)_
  - Yes · No
- **36. What is your source of information about UHC?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/ facility · LGU/ Barangay · I don't know · Other (Specify)
- **37. What is your understanding about UHC?**  _(select all that apply)_
  - Protection from financial risk/decreased out-of-pocket spending · Access to quality and affordable health care goods and services · Automatic enrollment into PhilHealth · Primary care provider for every Filipino · I don't know · Other (Specify)

## D. PhilHealth Registration and Health Insurance

- **38. Are you currently registered with PhilHealth?**  _(select one)_
  - Yes · No · I don't know
- **39. How did you find out about how to register for PhilHealth?**  _(select one)_
  - PhilHealth representative · LGU · Primary care provider · Other health care provider · Employer · No one / self-registered · Barangay Health Worker · Friends / Family · Health center/facility · Other (Specify)
- **40. Who assisted you in the registration process?**  _(select one)_
  - PhilHealth representative · LGU · Primary care provider · Other health care provider · Employer · No one / self-registered · Barangay Health Worker · Friends / Family · Health center/facility · Other (Specify)
- **41. Did you have any difficulties in the registration process?**  _(select one)_
  - Yes · No
- **42. What did you find difficult about the process?**  _(select all that apply)_
  - Unclear process · Took a long time · Did not know where to ask for help · Had to travel a long way · No valid ID · Did not know the required documents to register · I don't know · Other (Specify)
- **43. Would you know where to go to seek assistance during registration?**  _(select one)_
  - Yes · No
- **44. Where would you go to seek assistance?**  _(select one)_
  - PhilHealth representative · LGU · Primary care provider · Other health care provider · Employer · No one / self-registered · Barangay Health Worker · Friends / Family · Health center/facility · Other (Specify)
- **45. What category of member are you?**  _(select one)_
  - Formal economy (i.e., individuals working in the government or private sector based in the country) · Informal economy (i.e., unemployed, self-employed, informal workers, Filipinos with dual citizenship, naturalized Filipino citizens, citizens of other countries working and/or residing in the Philippines) · Indigent (i.e., individuals who have no visible means of income, or whose income is insufficient for family subsistence based on DSWD's specific criteria) · Sponsored (i.e., members whose contributions are being paid for by another individual, government agencies, or private entities. Includes some low-income citizens that are not indigent e.g. BHWs, PWDs) · Lifetime member (i.e., individuals aged 60 years and above, uniformed personnel aged 56 years and above, and SSS underground miner-retirees aged 55 years and above and paid at least 120 monthly contributions with PhilHealth and the former Medicare... · Senior citizen (i.e., residents of the Philippines, aged sixty (60) years or above and are not currently covered by any membership category of PhilHealth and qualified dependents of senior citizen members who are also senior citizen themselves or... · Overseas Filipino Worker (OFW) · Qualified dependents (i.e., those whose contributions are declared and covered by a principal member) · I don't know · Other (Specify)
- **46. What are some of the benefits that come with being a PhilHealth member?**  _(select all that apply)_
  - No balance billing for basic ward accommodation · Subsidized inpatient services · Subsidized outpatient services · There are no benefits to being a member · I don't know · Other (Specify)
- **47. Awareness of PhilHealth package**  _(select one)_
  - Yes · No
- **48. Do you pay PhilHealth premiums every month?**  _(select one)_
  - Yes, I pay directly · Yes, my employer pays · No, I do not pay premiums
- **49. Do you find it difficult to pay your PhilHealth premium every month?**  _(select one)_
  - Yes · No
- **50. Why did you find it difficult?**  _(select all that apply)_
  - Cannot afford the premium · Payment options are inconvenient · No time to pay · Don't see value in paying · System of PhilHealth is unreliable/usually down · I don't know · Other (Specify)
- **51. Are you registered with another health insurance plan?**  _(select one)_
  - Yes · No
- **52. Which health insurance plan/s are you enrolled in?**  _(select all that apply)_
  - GSIS · SSS · Private Insurance · HMO · Pag-ibig · I don't know · Others (specify)

## E. Primary Care Utilization

- **53. Do you have a primary care provider?**  _(select one)_
  - Yes · No
- **54. Who is your main primary care provider?**  _(select one)_
  - General practitioner · Specialty Care Provider/ Specialist · Both · Other (specify) · None
- **55. Is the location of your main primary care provider convenient for you?**  _(select one)_
  - Yes · No
- **56. Is your main primary care provider's clinic hours (time that your provider/s is/are open for medical appointments) convenient for you?**  _(select one)_
  - Yes · No
- **57. Is the usual wait for setting an appointment with your main primary care provider convenient for you?**  _(select one)_
  - Yes · No
- **58. Wait time to set appointment with main primary care provider**  _(number)_
- **59. What mode/s of communication was/were available to you when scheduling a consultation with your main primary care provider?**  _(select all that apply)_
  - Face-to-face · Teleconsultation · Landline · Cellphone · Video Conference
- **60. If teleconsultation was available, did you succeed in using the teleconsult? (scheduling)**  _(select one)_
  - Yes · No
- **61. What mode/s of communication was/were available to you when consulting with your main primary care provider?**  _(select all that apply)_
  - Face-to-face · Teleconsultation · Landline · Cellphone · Video Conference
- **62. If teleconsultation was available, did you succeed in using the teleconsult? (consultation)**  _(select one)_
  - Yes · No
- **63. In the past 12 months, do you have a clinic, or health center that you usually go to?**  _(select one)_
  - Yes · No
- **64. What is the name of the facility?**  _(text)_
- **65. If none, why do you not have a usual clinic, or health center that you usually go to?**  _(select all that apply)_
  - I don't get sick · I recently moved into the area · It's expensive · I can treat myself · I don't know where to go for care · I don't know · Other (Specify)
- **66. Is [facility_name_input] the facility you usually go to for general health concerns?**  _(select one)_
  - Yes · No
- **67. Why did you go to this facility instead of your usual facility?**  _(select all that apply)_
  - This facility is more accessible than my usual facility (i.e., nearer, has more transportation options to get to, and cheaper to travel to) · Needed a service/specialist not available at my usual facility · Recommended by friends/family · Wanted to try another facility than my usual · Prefer this facility than my usual · This was referred to me by my usual facility · Usual facility is closed for today · Other (Specify)
- **68. What is the type of health facility that you usually go to?**  _(select one)_
  - YAKAP/Konsulta or primary care provider · Barangay Health Center/ Barangay Health Station · Rural Health Unit / Urban Health Center · Public Hospital · Private Hospital · Private Clinic · Traditional Healer or Manghihilot/ Albularyo · I don't know · Other (specify)
- **69. How long does it take you to travel to the health facility you usually go to**  _(number)_
- **70. What mode/s of transportation do you use when travelling to the health facility that you usually go to?**  _(select all that apply)_
  - Walk · Bike · Public Bus · Jeepney · Tricycle · Car (including private taxi/cab) · Motorcycle · Boat · Taxi · Pedicab · E-bike · Other (Specify)
- **71. What is the type of the primary care facility nearest to your house?**  _(select one)_
  - Barangay Health Center/ Barangay Health Station · Rural Health Unit / Urban Health Center · Public Hospital · Private Hospital · Private Clinic · Traditional Healer or Manghihilot/ Albularyo · I don't know · Other (specify)
- **72. How long does it take you to travel from your house when going to the nearest primary care facility?**  _(number)_
- **73. What mode/s of transportation do you use when travelling to the nearest primary care facility?**  _(select all that apply)_
  - Walk · Bike · Public Bus · Jeepney · Tricycle · Car (including private taxi/cab) · Motorcycle · Boat · Taxi · Pedicab · E-bike · Other (Specify)
- **74. Have you heard of the term "YAKAP/ Konsulta package"?**  _(select one)_
  - Yes · No
- **75. What are your sources of information about the YAKAP/Konsulta package?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **76. What is your understanding about the YAKAP/Konsulta package?**  _(select all that apply)_
  - Free primary care consultation (with a registered YAKAP/Konsulta provider) · Free health risk screening and assessment (with a registered YAKAP/Konsulta provider) · Free selected laboratory / diagnostics examination · Free selected drugs and medicines · There are no benefits of the package · I don't know · Other (Specify)
- **77. Are you registered with a YAKAP/Konsulta package provider?**  _(select one)_
  - Yes · No · I've never heard of it · I don't know
- **78. When did you register with a YAKAP/Konsulta package provider?**  _(select one)_
  - Within the past six (6) months · More than six (6) months but less than one (1) year ago · One (1) year but less than two (2) years ago · Two (2) years ago or more
- **79. Since registering, have you had an appointment with your YAKAP/Konsulta package provider?**  _(select one)_
  - Yes · No
- **80. When you have a health problem, do you know how to book an appointment at your YAKAP/Konsulta package provider?**  _(select one)_
  - Yes · No
- **81. Was that appointment for a general check-up (i.e. not related to an illness or injury)?**  _(select one)_
  - Yes · No
- **82. Why are you NOT registered with a YAKAP/Konsulta package provider?**  _(select all that apply)_
  - Don't know what a YAKAP/Konsulta provider is · Don't trust PhilHealth · Don't know how to register · Registration is confusing/time-consuming/inconvenient · Intend to register but do not have found a time to do it. · YAKAP/Konsulta is not available in my local area · Already have a usual primary care provider that I go to · Don't have the required PhilHealth ID to register for YAKAP/Konsulta · Don't have the other requirements to register · I don't know · Other (specify)

## F. Patient's Health-Seeking Behavior

- **83. What best describes why the patient visited a health facility (e.g. RHU, health center, clinic, hospital)?**  _(select one)_
  - Consultation for new health problem · Consultation to follow-up an ongoing health problem · For tests/diagnostics only · For a general check-up · To get a health certificate/administrative reason · For immunizations/vaccinations · My doctor transferred to this health facility · Other (Specify)
- **84. What type of service did the patient usually access?**  _(select one)_
  - Outpatient care (Consultation, procedure, or treatment where the patient visits and leaves within the same day) · Inpatient care (Care provided in hospital or another facility where the patient is admitted for at least one night) · Emergency care (Care for serious illnesses or injuries that need immediate medical attention; usually provided in an emergency room or ER) · Primary care consultation · Other (Specify)
- **85. What condition/s do/es the patient usually visit the facility for?**  _(select all that apply)_
  - Upper respiratory infection · Hypertension · Immunization · Pregnancy or birth · Flu · Fever · Joint and muscle pain · Asthma or COPD (chronic breathing problem, not cancer) · Diabetes · Heart problem · Kidney problem /Dialysis · Cancer (any) · Gastro problem (vomiting, diarrhea etc.) · Other infection (e.g. urine, skin, other virus etc.) · Accident/injury (e.g. wound/broken bone) · Dental · ENT (problem with ear/nose/throat) · Allergy · No condition - Regular check-up only · Other (Specify)
- **86. Which of the following happened during the patient's most recent visit?**  _(select all that apply)_
  - Saw a doctor · Saw a nurse/midwife · Saw any other healthcare worker/member of medical staff · Had basic tests done (e.g. blood pressure check, height/weight) · Had any laboratory tests done (e.g. blood, urine sample) · Had any imaging done (e.g. ultrasound, Xray, CT) · Prescribed medication · Had any minor procedure/surgery done · Picked up medical certificate/other administration · Was admitted for confinement
- **87. Apart from this visit, has the patient done anything else to improve his/her health condition or address his/her health concern?**  _(select all that apply)_
  - Visited other healthcare facility · Sought alternative care (Healthcare apart from medical doctors or the formal healthcare system; such as reflexology... · Sought telemedicine (Remote diagnosis and treatment of patients by means of telecommunications technology) · Used home care (Healthcare services and support provided to individuals in their own homes) · Bought medicine from a pharmacy · Did not seek other forms of care · Other (Specify)

## G. Outpatient Care

- **88. Why are you visiting [FACILITY_NAME_INPUT] for consultation/advice or treatment?**  _(select one)_
  - Sick/Injured · Prenatal/Post-natal Check-up · Gave Birth · Dental check-up · Medical check-up · Medical requirement · NHTS/CCT/4Ps Requirement · Other (specify)
- **89. Were you advised for hospitalization / to be admitted in the hospital?**  _(select one)_
  - Yes · No
- **90. What were the reasons why you were not confined/ admitted in a hospital/clinic?**  _(select all that apply)_
  - Facility is far · No money · Worried about treatment cost · Home remedy is available · Health facility is not PhilHealth accredited · No need/regular check-up only · Other (specify)
- **91. Do you usually avail consultation services for outpatient care?**  _(select one)_
  - Yes · No
- **92. Cost of consultation**  _(select one)_
  - Yes · No
- **93. Did you have any of the following laboratory tests done during your outpatient care?**  _(select all that apply)_
  - CBC with platelet count · Urinalysis · Fecalysis · Sputum Microscopy · Fecal Occult Blood · Pap smear · Lipid profile · FBS · OGTT (Oral glucose tolerance tests) · ECG · Chest X-Ray · Creatinine · HbA1c · Abdominal ultrasound · Dental Services · Other, specify: · None
- **94. Cost of laboratory test/s**  _(select one)_
  - Yes · No
- **95. Were you prescribed medicine/s after your check-up?**  _(select one)_
  - Yes · No
- **96. Amount spent for prescribed medicines**  _(select one)_
  - Yes · No
- **97. What was the final amount you paid in cash for your outpatient care? (Amount in Pesos)**  _(number)_
- **97.1 Other items included in the bill**  _(select one)_
  - Yes · No
- **97.2 Other expenses during OPD visit not in bill**  _(select one)_
  - Yes · No
- **98. Used to pay for medical costs**  _(select one)_
  - Yes · No
- **99. Have you heard about Bagong Urgent Care and Ambulatory Services (BUCAS) center?**  _(select one)_
  - Yes · No
- **100. If yes, what are your sources of information about this BUCAS center?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **101. What is your understanding about a BUCAS center?**  _(select all that apply)_
  - Provides urgent care for non-life-threatening/serious conditions · Offers outpatient and ambulatory health services · Helps reduce overcrowding in hospitals · Allows access to timely medical consultation and treatment · Other (specify)
- **102. Have you accessed the services in a BUCAS center?**  _(select one)_
  - Yes · No
- **103. If yes, which service/s did you avail?**  _(select all that apply)_
  - Medical consultation for urgent or minor conditions · Outpatient or ambulatory care services · Basic diagnostic services (e.g., laboratory tests, X-ray) · Minor procedures or treatments · Referral to higher-level health facilities · I don't know · Other (specify)
- **104. Without BUCAS Center, where would you have gone?**  _(select one)_
  - Another DOH hospital · Private clinic/hospital · LGU hospital · Rural Health Unit / Health Center · Would not seek care · Others

## H. Inpatient Care

- **105. Why are you confined in the hospital?**  _(select one)_
  - Sick · Injured · Gave birth · Executive check-up · Other (specify)
- **106. How long were you confined?**  _(number)_
- **107. Total bill for confinement**  _(select one)_
  - Yes · No
- **108. Other than the medicine/s indicated in the hospital bill, did the patient buy medicine/s from any pharmacy/facility outside the hospital?**  _(select one)_
  - Yes · No
- **109. Amount paid for medicines outside the hospital**  _(select one)_
  - Yes · No
- **110. Other than the laboratory service/s indicated in the hospital bill, did the patient pay for other service/s outside the hospital?**  _(select one)_
  - Yes · No
- **111. If yes, what are those services?**  _(text)_
- **112. Amount paid for services outside the hospital**  _(select one)_
  - Yes · No
- **113. Used to pay for hospital bill**  _(select one)_
  - Yes · No
- **114. Why did you not avail of PhilHealth benefits? (If PhilHealth was not availed in 113)**  _(select all that apply)_
  - Not a PhilHealth member · PhilHealth member but not eligible for benefits · Probably used PhilHealth but cannot remember amount because benefit was deducted upon discharge from hospital · Too many requirements to comply with before can avail · Limited hospitalization benefits · Claims processing too long · Other (specify)
- **115. What was the final amount you paid in cash at the hospital cashier upon discharge? (Amount in Pesos)**  _(number)_
- **115.1 Other items included in the bill**  _(select one)_
  - Yes · No
- **115.2 Other expenses during confinement not in bill**  _(select one)_
  - Yes · No

## I. Financial Risk Protection

- **116. Have you heard of the No Balance Billing (NBB)?**  _(select one)_
  - Yes · No · I don't know
- **117. If yes, what are your sources of information about NBB?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **118. What is your understanding about NBB?**  _(select all that apply)_
  - Patient does not pay any hospital bill · PhilHealth will cover cost of treatment · Medicine and service are already included · No cash payment required upon discharge · Applies only to certain patients or hospitals · Bills are settled between the hospital and PhilHealth · Patients should not be charged extra fees · I don't know · Other (Specify)
- **119. Have you heard of the Zero Balance Billing (ZBB)?**  _(select one)_
  - Yes · No · I don't know
- **120. If yes, what are your sources of information about ZBB?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **121. What is your understanding about ZBB?**  _(select all that apply)_
  - Patient does not pay any hospital bill · PhilHealth will cover cost of treatment · Medicine and service are already included · No cash payment required upon discharge · Applies only to PhilHealth members and DOH-run hospitals · Bills are settled between the hospital and PhilHealth · Patients should not be charged extra fees · I don't know · Other (Specify)
- **122. Were you informed about ZBB upon admission?**  _(select one)_
  - Yes · No
- **123. To what extent did ZBB reduce your financial burden?**  _(select one)_
  - ZBB significantly reduced my financial burden by covering my expenses · It helped lessen some costs, but I still incurred Out-of-Pocket (OOP) expenses · ZBB provided some financial relief, though the support was limited compared to my total needs · ZBB did not make a noticeable difference in my financial situation
- **124. Have you heard of the Medical Assistance for Indigent and Financially Incapacitated Patients (MAIFIP)? (SKIP IF ANSWERED MAIFIP IN Q113)**  _(select one)_
  - Yes · No · I don't know
- **125. What are your sources of information about MAIFIP?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **126. Did you avail of MAIFIP in this last confinement?**  _(select one)_
  - Yes · No
- **127. If you availed MAIFIP, did you have to make any out-of-pocket payment?**  _(select one)_
  - Yes · No
- **128. Which items did you have to pay for out-of-pocket?**  _(select all that apply)_
  - Drugs · Laboratory · Professional Fees · Accommodation
- **129. Why did you not avail of MAIFIP during this last confinement?**  _(select all that apply)_
  - Not eligible · Too complicated · I don't like to stay in basic ward · There is no available basic ward
- **130. Have you or your household had to reduce spending on things you need (such as food, housing, or utilities) because of this health expenditure in the last 1 month?**  _(select one)_
  - Yes · No · Don't know · Refused to answer

## J. Satisfaction on Amenities and Medical Care

- **131. Satisfaction with cleanliness and comfort**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable
- **132. Satisfaction with cleanliness and comfort**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable
- **133. Satisfaction with cleanliness and comfort**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable
- **134. Satisfaction with cleanliness and comfort**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable
- **135. Were you satisfied with the overall time spent from registration to exiting the facility? (For inpatients only)**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable
- **136. In most recent visit, how often did the staff treat you with courtesy and respect?**  _(select one)_
  - Never · Sometimes · Usually · Always · I don't know
- **137. In most recent visit, how often did the staff listen carefully to what you say or ask?**  _(select one)_
  - Never · Sometimes · Usually · Always · I don't know
- **138. In most recent visit, how often did the staff explain your condition and procedures in a way you can understand?**  _(select one)_
  - Never · Sometimes · Usually · Always · I don't know
- **139. In most recent visit, how often did the staff give you the chance to make decisions about your treatment?**  _(select one)_
  - Never · Sometimes · Usually · Always · I don't know
- **140. In most recent visit, how often did the staff ask you for your consent before performing any treatments or tests?**  _(select one)_
  - Never · Sometimes · Usually · Always · I don't know
- **141. In your most recent visit, did the staff assure you that information about the patient's condition will be kept confidential?**  _(select one)_
  - Yes · No · I don't know
- **142. In your most recent visit, did the staff respect your privacy during the physical consultation?**  _(select one)_
  - Yes · No · I don't know
- **143. Overall, would you recommend [facility_name_input] to a friend or relative?**  _(select one)_
  - Yes · No
- **144. How would the patient rate the quality of care you received at [facility_name_input]?**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable

## K. Access to Medicines

- **145. How often do you purchase or receive medicines?**  _(select one)_
  - Weekly · Bi-weekly · Monthly · Rarely · Never
- **146. Was the most recent medicine purchased prescribed by a doctor or over-the-counter (OTC) medicine (no need for a prescription)?**  _(select one)_
  - Prescribed by a doctor · Over-the-counter medicine · Purchased both prescribed medicine and OTC medicine · I don't know
- **147. What are the medications that you usually take?**  _(text)_
- **148. What are the medical conditions that you take the medicines for?**  _(select one)_
  - Upper respiratory infection · Hypertension · Immunization · Pregnancy or birth · Flu · Fever · Joint and muscle pain · Asthma or COPD (chronic breathing problem, not cancer) · Diabetes · Heart problem · Kidney problem /Dialysis · Cancer (any) · Gastro problem (vomiting, diarrhea, etc.) · Other infection (e.g. urine, skin, other virus etc.) · Accident/injury (e.g. wound/broken bone) · Dental · ENT (problem with ear/nose/throat) · Allergy · No condition - Regular check-up only · Other (Specify)
- **149. Where do you usually buy or receive your medicines? Select all that apply.**  _(select all that apply)_
  - Public Hospital · Private Hospital · Chain Pharmacies (e.g. Mercury Drug, Watsons, TGP, Generika) · Local pharmacies · Online stores (e.g. Shopee, Lazada) · Barangay Health Station · Rural Health Unit or City Health Office · Other (specify)
- **150. Travel time from home to nearest pharmacy**  _(number)_
- **151. How easy is it for you to access a pharmacy or drugstore?**  _(select one)_
  - Very difficult · Difficult · Neutral · Easy · Very easy
- **152. Have you heard of the Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT) Package, which is part of PhilHealth's YAKAP/Konsulta or primary care benefit package?**  _(select one)_
  - Yes · No
- **153. If yes, what are your sources of information for GAMOT Package?**  _(select all that apply)_
  - News · Legislation · Social Media · Friends / Family · Health center/facility · LGU/Barangay · I don't know · Other (Specify)
- **154. What is your understanding of the GAMOT Package?**  _(select all that apply)_
  - Provides free or affordable medicines for outpatients · Ensures continuous availability of essential medicines · Helps reduce out-of-pocket expenses for medicines · Supports treatment of common illnesses and chronic conditions · I don't know · Other (specify)
- **155. Did you get the medicines from the GAMOT Package during the past 6 months?**  _(select one)_
  - Yes · No
- **156. What are the medications that you obtained from the GAMOT Package? [LIST]**  _(text)_
- **157. Where did you get the rest of the medicines? Select all that apply.**  _(select all that apply)_
  - Purchased from pharmacy · Purchased from public hospital · Purchased from private hospital · Purchased from primary care provider (PCP) · Received from PCP for free · Received from LGU for free · Received from public hospital for free · Received from private hospital for free · Other (Specify)
- **158. Do you know the difference between a 'branded' and a 'generic' medicine?**  _(select one)_
  - Yes · No
- **159. Was/were the medicine/s you bought outside of GAMOT pharmacy branded or generic?**  _(select one)_
  - Branded · Generic · Both branded and generic · Don't know the difference · Not applicable
- **160. If generic, why did you buy generic medicine?**  _(select all that apply)_
  - Lower cost · Prescribed by doctor · Readily available · Given for free · More or as effective as branded medicine · I don't know · Other (Specify)
- **161. If branded, why did you buy branded medicine?**  _(select all that apply)_
  - Branded medicine is more effective than generic · Not aware of generic option · Prescribed by doctor · Given for free · Prefer branded over generic option · I don't know · Other (Specify)

## L. Experiences and Satisfaction on Referrals

- **162. Based on your most recent visit/confinement at [facility_name_input], did a healthcare worker refer you to another facility or specialist for further care or specialized care?**  _(select one)_
  - Yes · No
- **163. What type of care was the referral for?**  _(select all that apply)_
  - Outpatient care (Consultation, procedure, or treatment where the patient visits and leaves within the same day) · Emergency care (Care for serious illnesses or injuries that need immediate medical attention; usually provided in an emergency room or ER) · Inpatient care (Care provided in hospital or another facility where the patient is admitted for at least one night) · Dental care (Medical care for your teeth, such as cleanings, fillings, etc.) · Other facility visits (Care that is provided in a facility that is not a health center or hospital, such as independent diagnostic centers, TB dispensaries, etc.) · Special therapy visits (Rehabilitation care or services, such as occupational therapy, physical therapy, psychological and behavioral rehabilitation, prosthetics and orthotics rehabilitation, or speech... · Alternative care (Healthcare apart from medical doctors or the formal health care system; such as reflexology, acupuncture, massage therapy, herbal medicines, etc.) · Outreach / medical missions (Care provided by the government or an NGO through an outreach or medical mission within a community) · Home healthcare (Care that is administered at the patient's home, such as birth delivery, checkups, immunization, rehabilitation, etc.) · Telemedicine (Remote diagnosis and treatment of patients by means of telecommunications technology) · None of the above · Other (Specify)
- **164. What kind of specialist did they recommend?**  _(select one)_
  - No specialty · Anesthesia · Dermatology · Emergency Medicine · Family Medicine · General Surgery · Internal Medicine · Neurology · Nuclear Medicine · Obstetrics and Gynecology · Occupational Medicine · Ophthalmology · Orthopedics · Otorhinolaryngology (ENT) · Pathology · Pediatrics · Physical and Rehabilitation Medicine · Psychiatry · Public health · Radiology · Research · I don't know · Other (Specify)
- **165. How did they refer you to the doctor?**  _(select one)_
  - Physical referral slip · E-referral · Phone call from referring facility to receiving facility · I don't know · Other (Specify)
- **166. Did they discuss with you the different places you could have gone to address your health problem?**  _(select one)_
  - Yes · No
- **167. Did they help you make the appointment for that visit?**  _(select one)_
  - Yes · No
- **168. Did they write down any information for the specialist about the reason for that visit?**  _(select one)_
  - Yes · No
- **169. Have you visited the referred hospital or facility after the referral was made?**  _(select one)_
  - Yes · No, I'm not planning to · Not yet, but I'm planning to
- **170. After your visit to the referral hospital/ specialist, did they follow up with you about what happened at the visit?**  _(select one)_
  - Yes · No
- **171. Why are you NOT planning to visit?**  _(select all that apply)_
  - Facility is too far · Do not trust the referred facility · No time · Worried about additional costs · Not needed · Don't know how to get to facility · Other (Specify)
- **172. Was the visit to [facility_name_input] a referral from your primary care facility?**  _(select one)_
  - Yes · No
- **173. Does your primary care provider know that you made the visit?**  _(select one)_
  - Yes · No · I don't know
- **174. Did your primary care provider discuss with you different places you could have gone to get help with your problem?**  _(select one)_
  - Yes · No
- **175. Did your primary care provider (PCP) or someone working with your PCP help you make the appointment for that visit?**  _(select one)_
  - Yes · No
- **176. Did your primary care provider write down any information for the specialist about the reason for that visit?**  _(select one)_
  - Yes · No
- **177. As it was not a referral, why did you decide to visit a hospital?**  _(select all that apply)_
  - Referred by other specialist (doctor in another hospital) · Nearest facility to house · Facility is usual source of care · Facility is the only place that can perform a certain test · Referred by BHW/nurse/midwife/other community health professional · Referred by family / friends · Facility offers subsidized or free health services · ZBB eligibility · I don't know · Other (Specify)
- **178. Overall, how would you rate your experience with the referral process?**  _(select one)_
  - Very Satisfied · Satisfied · Neither Satisfied nor Dissatisfied · Dissatisfied · Very Dissatisfied · Not applicable

*Total: 226 questions/fields across the instrument.*
