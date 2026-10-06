import os
import re
import json
import time
import urllib.parse
from io import BytesIO
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# In-memory cache for disease information to avoid redundant network calls
_DISEASE_CACHE = {}

# 14 Supported Crops and their respective classes in the 38-class dataset
CROP_CATALOG = {
    "apple": {
        "name": "Apple",
        "icon": "🍎",
        "classes": [
            "Apple___Apple_scab",
            "Apple___Black_rot",
            "Apple___Cedar_apple_rust",
            "Apple___healthy"
        ],
        "description": "Orchard tree susceptible to apple scab, cedar rust, and black rot."
    },
    "blueberry": {
        "name": "Blueberry",
        "icon": "🫐",
        "classes": ["Blueberry___healthy"],
        "description": "Acidic-soil perennial berry crop."
    },
    "cherry": {
        "name": "Cherry",
        "icon": "🍒",
        "classes": [
            "Cherry_(including_sour)___Powdery_mildew",
            "Cherry_(including_sour)___healthy"
        ],
        "description": "Stone fruit tree susceptible to powdery mildew fungal infection."
    },
    "corn": {
        "name": "Corn (Maize)",
        "icon": "🌽",
        "classes": [
            "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
            "Corn_(maize)___Common_rust_",
            "Corn_(maize)___Northern_Leaf_Blight",
            "Corn_(maize)___healthy"
        ],
        "description": "Cereal crop vulnerable to common rust, leaf blight, and Cercospora spots."
    },
    "grape": {
        "name": "Grape",
        "icon": "🍇",
        "classes": [
            "Grape___Black_rot",
            "Grape___Esca_(Black_Measles)",
            "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
            "Grape___healthy"
        ],
        "description": "Vineyard fruit prone to black rot, Esca measles, and leaf blight."
    },
    "orange": {
        "name": "Orange / Citrus",
        "icon": "🍊",
        "classes": ["Orange___Haunglongbing_(Citrus_greening)"],
        "description": "Citrus orchard fruit prone to Huanglongbing (Citrus Greening)."
    },
    "peach": {
        "name": "Peach",
        "icon": "🍑",
        "classes": [
            "Peach___Bacterial_spot",
            "Peach___healthy"
        ],
        "description": "Stone fruit crop affected by bacterial shot-hole spot."
    },
    "pepper": {
        "name": "Pepper (Bell)",
        "icon": "🫑",
        "classes": [
            "Pepper,_bell___Bacterial_spot",
            "Pepper,_bell___healthy"
        ],
        "description": "Solanaceous vegetable vulnerable to bacterial leaf spots."
    },
    "potato": {
        "name": "Potato",
        "icon": "🥔",
        "classes": [
            "Potato___Early_blight",
            "Potato___Late_blight",
            "Potato___healthy"
        ],
        "description": "Underground tuber crop vulnerable to early blight and late blight."
    },
    "raspberry": {
        "name": "Raspberry",
        "icon": "🍇",
        "classes": ["Raspberry___healthy"],
        "description": "Woody perennial cane fruit."
    },
    "soybean": {
        "name": "Soybean",
        "icon": "🌱",
        "classes": ["Soybean___healthy"],
        "description": "Oilseed legume vital for nitrogen fixation and grain yield."
    },
    "squash": {
        "name": "Squash",
        "icon": "🎃",
        "classes": ["Squash___Powdery_mildew"],
        "description": "Cucurbit crop prone to powdery mildew white powdery patches."
    },
    "strawberry": {
        "name": "Strawberry",
        "icon": "🍓",
        "classes": [
            "Strawberry___Leaf_scorch",
            "Strawberry___healthy"
        ],
        "description": "Low-growing berry plant susceptible to fungal leaf scorch."
    },
    "tomato": {
        "name": "Tomato",
        "icon": "🍅",
        "classes": [
            "Tomato___Bacterial_spot",
            "Tomato___Early_blight",
            "Tomato___Late_blight",
            "Tomato___Leaf_Mold",
            "Tomato___Septoria_leaf_spot",
            "Tomato___Spider_mites Two-spotted_spider_mite",
            "Tomato___Target_Spot",
            "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
            "Tomato___Tomato_mosaic_virus",
            "Tomato___healthy"
        ],
        "description": "High-value horticultural crop with 10 distinct health and disease classes."
    },

    # =========================================================================
    # EXPANDED GLOBAL CROPS (Diagnosed via Universal Multimodal AI Vision)
    # =========================================================================
    "rice": {
        "name": "Rice (Paddy)",
        "scientific": "Oryza sativa",
        "icon": "🌾",
        "is_universal": True,
        "classes": ["Blast", "Bacterial Leaf Blight", "Brown Spot", "Sheath Blight", "Healthy"],
        "description": "Global staple grain prone to blast, bacterial leaf blight, and brown spot."
    },
    "wheat": {
        "name": "Wheat",
        "scientific": "Triticum aestivum",
        "icon": "🌾",
        "is_universal": True,
        "classes": ["Yellow Rust (Stripe)", "Brown Rust (Leaf)", "Powdery Mildew", "Septoria", "Healthy"],
        "description": "Cereal staple crop susceptible to stripe rust, leaf rust, and powdery mildew."
    },
    "cotton": {
        "name": "Cotton",
        "scientific": "Gossypium",
        "icon": "☁️",
        "is_universal": True,
        "classes": ["Bacterial Blight", "Alternaria Leaf Spot", "Fusarium Wilt", "Healthy"],
        "description": "Fiber cash crop affected by angular leaf spot and boll rot."
    },
    "sugarcane": {
        "name": "Sugarcane",
        "icon": "🎋",
        "scientific": "Saccharum officinarum",
        "is_universal": True,
        "classes": ["Red Rot", "Smut", "Rust", "Yellow Leaf Disease", "Healthy"],
        "description": "Tropical sucrose crop susceptible to red rot and smut."
    },
    "mango": {
        "name": "Mango",
        "scientific": "Mangifera indica",
        "icon": "🥭",
        "is_universal": True,
        "classes": ["Anthracnose", "Powdery Mildew", "Bacterial Canker", "Malformation", "Healthy"],
        "description": "King of fruits vulnerable to anthracnose, powdery mildew, and bacterial canker."
    },
    "banana": {
        "name": "Banana",
        "scientific": "Musa acuminata",
        "icon": "🍌",
        "is_universal": True,
        "classes": ["Black Sigatoka", "Panama Disease (Fusarium)", "Banana Bunchy Top Virus", "Healthy"],
        "description": "Tropical fruit crop affected by destructive black sigatoka and wilt."
    },
    "guava": {
        "name": "Guava",
        "scientific": "Psidium guajava",
        "icon": "🍈",
        "is_universal": True,
        "classes": ["Anthracnose", "Wilt", "Fruit Canker", "Healthy"],
        "description": "Subtropical fruit prone to guava wilt and anthracnose spot."
    },
    "papaya": {
        "name": "Papaya",
        "scientific": "Carica papaya",
        "icon": "🍈",
        "is_universal": True,
        "classes": ["Papaya Ringspot Virus", "Anthracnose", "Black Spot", "Healthy"],
        "description": "Fast-growing fruit tree vulnerable to ringspot potyvirus."
    },
    "lemon": {
        "name": "Lemon / Lime",
        "scientific": "Citrus limon",
        "icon": "🍋",
        "is_universal": True,
        "classes": ["Citrus Canker", "Anthracnose", "Greasy Spot", "Healthy"],
        "description": "Acid citrus tree prone to Xanthomonas bacterial canker."
    },
    "onion": {
        "name": "Onion / Garlic",
        "scientific": "Allium cepa",
        "icon": "🧅",
        "is_universal": True,
        "classes": ["Purple Blotch", "Downy Mildew", "Stemphylium Leaf Blight", "Healthy"],
        "description": "Allium vegetable crop vulnerable to Alternaria purple blotch."
    },
    "rose": {
        "name": "Rose",
        "scientific": "Rosa",
        "icon": "🌹",
        "is_universal": True,
        "classes": ["Black Spot", "Powdery Mildew", "Rose Rust", "Downy Mildew", "Healthy"],
        "description": "Ornamental flora prone to Diplocarpon rosae black spot and rust."
    },
    "coffee": {
        "name": "Coffee",
        "scientific": "Coffea arabica",
        "icon": "☕",
        "is_universal": True,
        "classes": ["Coffee Leaf Rust (Roya)", "Coffee Berry Disease", "Cercospora Leaf Spot", "Healthy"],
        "description": "High-altitude beverage crop threatened by Hemileia vastatrix rust."
    },
    "tea": {
        "name": "Tea",
        "scientific": "Camellia sinensis",
        "icon": "🍵",
        "is_universal": True,
        "classes": ["Blister Blight", "Grey Blight", "Brown Blight", "Healthy"],
        "description": "Perennial shrub prone to Exobasidium blister blight."
    },
    "chili": {
        "name": "Chili / Hot Pepper",
        "scientific": "Capsicum annuum",
        "icon": "🌶️",
        "is_universal": True,
        "classes": ["Chili Leaf Curl Virus", "Anthracnose / Dieback", "Bacterial Leaf Spot", "Healthy"],
        "description": "Pungent spice crop affected by whitefly-transmitted leaf curl begomovirus."
    }
}

# Comprehensive Agronomic Database for all crop-disease combinations
AGRONOMIC_KNOWLEDGE_BASE = {
    "Apple_scab": {
        "wiki_page": "Venturia_inaequalis",
        "overview": "Apple scab is caused by the fungus Venturia inaequalis. It attacks both leaves and fruit, causing significant quality and yield loss in orchards.",
        "symptoms": [
            "Olive-green to dull dark brown velvety spots on upper leaf surfaces.",
            "Leaves turn yellow and drop prematurely during mid-summer.",
            "Dark, corky scabs and cracking on apple fruits."
        ],
        "organic_remedies": [
            "Apply wettable sulfur or copper-based sprays during the early green tip stage.",
            "Spray neem oil or potassium bicarbonate at first sign of lesions.",
            "Rake and shred or compost fallen apple leaves in autumn to eliminate overwintering spores."
        ],
        "chemical_treatments": [
            "Fungicides containing Myclobutanil, Mancozeb, or Captan.",
            "Apply protectant fungicides in early spring before rain events."
        ],
        "prevention": [
            "Plant scab-resistant cultivars (e.g., Liberty, Freedom, Enterprise).",
            "Prune tree canopy annually to promote rapid drying of foliage.",
            "Avoid overhead irrigation."
        ]
    },
    "Black_rot": {
        "wiki_page": "Botryosphaeria_obtusa",
        "overview": "Black rot (caused by Botryosphaeria obtusa or Guignardia bidwellii in grapes) causes leaf spot, canker on branches, and rot on fruits.",
        "symptoms": [
            "Small purple spots on leaves that enlarge into 'frog-eye' lesions with light brown centers.",
            "Fruit develops circular brown sunken spots with black concentric rings.",
            "Infected fruit shrivels into black, hard mummies."
        ],
        "organic_remedies": [
            "Copper hydroxide or liquid copper octanoate sprays.",
            "Promptly prune dead twigs, mummified fruits, and cankered branches."
        ],
        "chemical_treatments": [
            "Captan, Mancozeb, or Difenoconazole applied from bud break through post-bloom."
        ],
        "prevention": [
            "Remove and destroy all mummified fruit remaining on the plant or ground.",
            "Ensure proper vine/branch spacing for good air circulation."
        ]
    },
    "Cedar_apple_rust": {
        "wiki_page": "Gymnosporangium_juniperi-virginianae",
        "overview": "Cedar apple rust is a fungal disease caused by Gymnosporangium juniperi-virginianae requiring both juniper/cedar and apple trees to complete its life cycle.",
        "symptoms": [
            "Bright orange-yellow circular spots on the upper leaf surface.",
            "Small tube-like projections (aecia) under the leaf lesions shedding spores in mid-summer.",
            "Orange rust galls on nearby cedar trees."
        ],
        "organic_remedies": [
            "Sulfur sprays applied when apple flower buds first show pink color.",
            "Neem oil can offer light protection when applied early."
        ],
        "chemical_treatments": [
            "Fungicides containing Myclobutanil or Propiconazole applied at 7-10 day intervals during peak spore release."
        ],
        "prevention": [
            "Remove Eastern red cedar trees located within a 1-mile radius if feasible.",
            "Select rust-resistant apple varieties."
        ]
    },
    "Powdery_mildew": {
        "wiki_page": "Powdery_mildew",
        "overview": "Powdery mildew is a fungal disease affecting a wide range of crops including cherry, squash, grape, and apple. It thrives in high humidity and moderate temperatures.",
        "symptoms": [
            "White, talcum powder-like patches on young leaves, shoots, and fruit.",
            "Leaf distortion, curling, and stunted shoot growth.",
            "Premature defoliation in severe infestations."
        ],
        "organic_remedies": [
            "Potassium bicarbonate (3 tbsp per gallon of water) with horticultural oil.",
            "Diluted milk spray (40% milk, 60% water) exposed to bright sunlight.",
            "Neem oil or sulfur sprays."
        ],
        "chemical_treatments": [
            "Triazole fungicides (e.g., Tebuconazole, Myclobutanil) or Strobilurin fungicides (Azoxystrobin)."
        ],
        "prevention": [
            "Plant crops in full sun with adequate spacing for air movement.",
            "Avoid excessive nitrogen fertilization which promotes lush, susceptible foliage.",
            "Water plants at soil level to keep foliage dry."
        ]
    },
    "Cercospora_leaf_spot Gray_leaf_spot": {
        "wiki_page": "Cercospora_zeae-maydis",
        "overview": "Gray leaf spot of corn is caused by Cercospora zeae-maydis. It is a major foliar disease that severely restricts photosynthetic area.",
        "symptoms": [
            "Small rectangular tan lesions bounded by leaf veins.",
            "Lesions expand into long rectangular blocks up to 2-3 inches long.",
            "Whole leaf blighting, premature drying, and stalk lodging."
        ],
        "organic_remedies": [
            "Crop rotation with non-host crops like soybean or alfalfa.",
            "Bio-fungicides based on Bacillus subtilis."
        ],
        "chemical_treatments": [
            "Foliar fungicides such as Pyraclostrobin, Azoxystrobin, or Propiconazole applied between V12 and R2 stages."
        ],
        "prevention": [
            "Plant resistant corn hybrids.",
            "Till residues to accelerate decomposition of overwintering fungi."
        ]
    },
    "Common_rust": {
        "wiki_page": "Puccinia_sorghi",
        "overview": "Common rust in corn is caused by Puccinia sorghi, favored by cool temperatures (60-70°F) and high relative humidity.",
        "symptoms": [
            "Small circular to elongate cinnamon-brown pustules on both leaf surfaces.",
            "Pustules rupture the epidermis, releasing powdery rust-colored spores.",
            "Severely affected leaves yellow and die back."
        ],
        "organic_remedies": [
            "Sulfur-based fungicides at early symptom onset."
        ],
        "chemical_treatments": [
            "Strobilurin and triazole fungicides (Azoxystrobin + Propiconazole)."
        ],
        "prevention": [
            "Use hybrids with genetic resistance to Puccinia sorghi.",
            "Early planting can help crops mature before high spore populations arrive."
        ]
    },
    "Northern_Leaf_Blight": {
        "wiki_page": "Exserohilum_turcicum",
        "overview": "Northern Corn Leaf Blight (NCLB) is caused by Exserohilum turcicum. It creates large elliptical necrotic lesions.",
        "symptoms": [
            "Long, elliptical, cigar-shaped grayish-green to tan lesions (1 to 6 inches long).",
            "Dark spore masses visible within lesions during wet weather.",
            "Extensive leaf destruction leading to ear fill reduction."
        ],
        "organic_remedies": [
            "Trichoderma-based biocontrol agents.",
            "Deep tillage of crop debris post-harvest."
        ],
        "chemical_treatments": [
            "Triazole and strobilurin mixtures (e.g., Pyraclostrobin + Fluxapyroxad)."
        ],
        "prevention": [
            "Choose resistant corn hybrids containing Ht genes.",
            "Rotate crops annually with non-grasses."
        ]
    },
    "Esca_(Black_Measles)": {
        "wiki_page": "Esca_(grape_disease)",
        "overview": "Esca is a complex fungal grapevine trunk disease that causes vascular degradation, leaf tiger-striping, and berry spotting.",
        "symptoms": [
            "'Tiger stripe' pattern with yellow and necrotic brown bands between green leaf veins.",
            "Small, dark purple spots on grape berries (measles).",
            "Sudden apoplexy (wilting and collapse of vines in hot weather)."
        ],
        "organic_remedies": [
            "Apply Trichoderma-based pruning wound sealants immediately after pruning.",
            "Remedial surgery to excise infected cordons or trunk sections."
        ],
        "chemical_treatments": [
            "Treat pruning wounds with protective fungicidal pastes (Thiophanate-methyl)."
        ],
        "prevention": [
            "Prune during dry weather in late winter.",
            "Disinfect pruning shears regularly between vines."
        ]
    },
    "Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "wiki_page": "Phaeoisariopsis_vitis",
        "overview": "Isariopsis leaf spot / leaf blight in grapes causes premature defoliation and reduces sugar accumulation.",
        "symptoms": [
            "Dark brown irregular spots with distinct chlorotic yellow halos on leaves.",
            "Underside of spots has a velvety, dark fungal growth.",
            "Leaves turn brittle and drop early."
        ],
        "organic_remedies": [
            "Bordeaux mixture or copper oxychloride sprays.",
            "Pruning lower leaves to increase ground clearance."
        ],
        "chemical_treatments": [
            "Mancozeb, Chlorothalonil, or Kresoxim-methyl."
        ],
        "prevention": [
            "Improve trellis aeration and light penetration.",
            "Collect and destroy fallen infected leaves."
        ]
    },
    "Haunglongbing_(Citrus_greening)": {
        "wiki_page": "Citrus_greening_disease",
        "overview": "Citrus greening (Huanglongbing) is a devastating bacterial infection caused by Candidatus Liberibacter and transmitted by the Asian citrus psyllid.",
        "symptoms": [
            "Blotchy mottle pattern on leaves, asymmetrical yellowing.",
            "Small, lopsided, bitter fruit that stays green at the bottom.",
            "Twig dieback, stunted growth, and eventual tree decline."
        ],
        "organic_remedies": [
            "Reflective ground mulch to deter citrus psyllids.",
            "Beneficial parasitoid wasps (Tamarixia radiata) for biological control."
        ],
        "chemical_treatments": [
            "Targeted insecticides for psyllid control (Imidacloprid, Thiamethoxam).",
            "Nutritional foliar sprays (zinc, iron, manganese) to sustain vigor."
        ],
        "prevention": [
            "Plant only certified disease-free nursery stock.",
            "Routinely scout and eliminate psyllid vectors immediately."
        ]
    },
    "Bacterial_spot": {
        "wiki_page": "Xanthomonas_campestris_pv._vesicatoria",
        "overview": "Bacterial spot attacks peppers, tomatoes, and peaches, caused by Xanthomonas species. It spreads rapidly in warm, rainy weather.",
        "symptoms": [
            "Small water-soaked circular or angular dark spots on foliage.",
            "Spots become necrotic with yellow haloes, leading to shot-hole effect or leaf drop.",
            "Rough, raised scabby lesions on fruits."
        ],
        "organic_remedies": [
            "Fixed copper sprays combined with mancozeb (where permitted) or Bacillus amyloliquefaciens.",
            "Garlic extract or horticultural oil sprays."
        ],
        "chemical_treatments": [
            "Copper bactericides combined with Mancozeb to overcome copper-resistant bacterial strains."
        ],
        "prevention": [
            "Use certified pathogen-free seed and transplants.",
            "Avoid overhead sprinkler irrigation; use drip irrigation.",
            "Do not work in fields when plants are wet."
        ]
    },
    "Early_blight": {
        "wiki_page": "Alternaria_solani",
        "overview": "Early blight is caused by the fungus Alternaria solani, affecting tomatoes and potatoes. It causes defoliation, stem lesions, and fruit rot.",
        "symptoms": [
            "Dark circular spots with concentric target-like rings on older leaves.",
            "Yellowing tissue surrounds each concentric spot.",
            "Progresses upwards from lower canopy, causing extensive defoliation."
        ],
        "organic_remedies": [
            "Copper sulfate or copper octanoate applied every 7-10 days.",
            "Neem oil and Bacillus subtilis sprays.",
            "Mulch around the base to prevent soil splash onto lower foliage."
        ],
        "chemical_treatments": [
            "Chlorothalonil, Mancozeb, or Azoxystrobin applied preventatively."
        ],
        "prevention": [
            "Prune lower leaves (bottom 12-18 inches) once plants are established.",
            "Rotate crops with non-solanaceous plants for at least 3 years.",
            "Stake and support tomato plants."
        ]
    },
    "Late_blight": {
        "wiki_page": "Phytophthora_infestans",
        "overview": "Late blight is a catastrophic plant disease caused by the oomycete Phytophthora infestans (responsible for the historic Irish Potato Famine).",
        "symptoms": [
            "Large, dark, water-soaked, irregular lesions on leaves and stems.",
            "Delicate white fungal-like growth on the undersides of leaves in humid conditions.",
            "Rapid collapse, browning, and death of entire plant canopy within days."
        ],
        "organic_remedies": [
            "Preventative copper hydroxide sprays before humid rainy periods.",
            "Destroy and bury or burn infected foliage immediately; do not compost."
        ],
        "chemical_treatments": [
            "Cymoxanil, Dimethomorph, Mandipropamid, or Chlorothalonil.",
            "Must be applied preventatively or at the absolute earliest detection."
        ],
        "prevention": [
            "Plant late blight-resistant potato and tomato varieties.",
            "Eliminate volunteer potatoes and cull piles from previous seasons.",
            "Monitor regional late blight forecasting alerts."
        ]
    },
    "Leaf_Mold": {
        "wiki_page": "Passalora_fulva",
        "overview": "Tomato leaf mold is caused by Passalora fulva (Fulvia fulva), common in high tunnels and greenhouses with high relative humidity.",
        "symptoms": [
            "Pale green or yellow spots on the upper leaf surface with indefinite borders.",
            "Dense, olive-green to grayish-brown velvety mold on the underside of corresponding spots.",
            "Leaves curl, wither, and drop prematurely."
        ],
        "organic_remedies": [
            "Bio-fungicides containing Bacillus amyloliquefaciens.",
            "Copper fungicides."
        ],
        "chemical_treatments": [
            "Chlorothalonil, Cyazofamid, or Difenoconazole."
        ],
        "prevention": [
            "Improve greenhouse ventilation and install circulation fans to keep humidity below 85%.",
            "Water at the base of plants early in the day."
        ]
    },
    "Septoria_leaf_spot": {
        "wiki_page": "Septoria_lycopersici",
        "overview": "Septoria leaf spot is caused by the fungus Septoria lycopersici, one of the most destructive leaf diseases of tomatoes.",
        "symptoms": [
            "Numerous small circular spots (1-3 mm) with dark brown margins and gray/tan centers.",
            "Tiny black speckles (pycnidia) visible in the centers of spots.",
            "Severe yellowing and rapid defoliation progressing upward from bottom."
        ],
        "organic_remedies": [
            "Copper fungicide sprays every 7-10 days in wet seasons.",
            "Apply straw mulch 2-3 inches thick to block fungal spores in soil."
        ],
        "chemical_treatments": [
            "Chlorothalonil or Mancozeb sprayed starting when first flower clusters open."
        ],
        "prevention": [
            "Remove lower foliage to eliminate splash zone.",
            "Practice 2 to 3-year crop rotation without nightshade crops."
        ]
    },
    "Spider_mites Two-spotted_spider_mite": {
        "wiki_page": "Tetranychus_urticae",
        "overview": "Two-spotted spider mites (Tetranychus urticae) are microscopic sap-sucking pests that flourish in hot, dry, and dusty conditions.",
        "symptoms": [
            "Fine pale yellow or bronze stippling / speckling on upper leaf surfaces.",
            "Fine silken webbing on the undersides of leaves and leaf stems.",
            "Leaves turn bronze, dry out, and drop."
        ],
        "organic_remedies": [
            "Insecticidal soap or horticultural oil spray covering both sides of leaves.",
            "Release predatory mites (Phytoseiulus persimilis or Neoseiulus californicus).",
            "Vigorous spray of plain water to dislodge mites and wash webbing away."
        ],
        "chemical_treatments": [
            "Miticides such as Bifenazate, Abamectin, or Spiromesifen (rotate modes of action to prevent resistance)."
        ],
        "prevention": [
            "Keep growing areas well-watered and reduce dust.",
            "Avoid broad-spectrum synthetic pyrethroids that kill natural mite predators."
        ]
    },
    "Target_Spot": {
        "wiki_page": "Corynespora_cassiicola",
        "overview": "Target spot is caused by the fungus Corynespora cassiicola, affecting tomatoes and soybeans in warm, humid climates.",
        "symptoms": [
            "Pinpoint brown spots that expand into circular lesions with light brown centers.",
            "Concentric rings resembling a target board with a yellow margin.",
            "Stem and blossom blight, accompanied by circular sunken fruit lesions."
        ],
        "organic_remedies": [
            "Copper-based bactericides/fungicides.",
            "Improve plant spacing for airflow."
        ],
        "chemical_treatments": [
            "Boscalid, Pyraclostrobin, Fluxapyroxad, or Chlorothalonil."
        ],
        "prevention": [
            "Stake and prune plants to improve airflow.",
            "Avoid overhead irrigation and sanitize stakes and cages."
        ]
    },
    "Tomato_Yellow_Leaf_Curl_Virus": {
        "wiki_page": "Tomato_yellow_leaf_curl_virus",
        "overview": "Tomato Yellow Leaf Curl Virus (TYLCV) is a devastating begomovirus transmitted by the sweetpotato whitefly (Bemisia tabaci).",
        "symptoms": [
            "Severe upward curling and cupping of leaf margins.",
            "Interveinal chlorosis (yellowing) on leaf margins.",
            "Severe stunting of young shoots, bush-like appearance, and flower drop."
        ],
        "organic_remedies": [
            "Yellow sticky traps to monitor and catch whiteflies.",
            "Neem oil, insecticidal soaps, or Beauveria bassiana for whitefly control.",
            "Remove and immediately bag/destroy infected plants."
        ],
        "chemical_treatments": [
            "Systemic insecticides targeting whitefly vectors (Dinotefuran, Acetamiprid)."
        ],
        "prevention": [
            "Plant TYLCV-resistant tomato cultivars (e.g., Tygress, Skyway).",
            "Use 50-mesh fine insect exclusion netting in nurseries and greenhouses."
        ]
    },
    "Tomato_mosaic_virus": {
        "wiki_page": "Tomato_mosaic_virus",
        "overview": "Tomato mosaic virus (ToMV) is a highly contagious tobamovirus that spreads mechanically through hands, tools, and seeds.",
        "symptoms": [
            "Mottled light and dark green mosaic patterns on leaves.",
            "Leaf distortion, blistering, and 'fern-leaf' thinning.",
            "Stunted plant growth and uneven fruit ripening with brown interior rings."
        ],
        "organic_remedies": [
            "No chemical cure exists for viral infections; immediately rogue out infected plants.",
            "Disinfect hands and tools with a 20% non-fat dry milk solution or 10% bleach."
        ],
        "chemical_treatments": [
            "No direct chemical antiviral treatments are effective; focus on hygiene and seed sanitation."
        ],
        "prevention": [
            "Use certified virus-free seed or resistant tomato varieties (marked 'T' or 'ToMV').",
            "Never smoke or use tobacco near tomato plants, as tobacco products carry the virus.",
            "Thoroughly sanitize gardening tools between rows."
        ]
    },
    "Leaf_scorch": {
        "wiki_page": "Diplocarpon_earlianum",
        "overview": "Leaf scorch in strawberries is caused by the fungus Diplocarpon earlianum. It damages photosynthetic leaf area and weakens runner production.",
        "symptoms": [
            "Numerous irregular purplish spots on the upper leaf surface.",
            "Spots enlarge and centers turn dark brown, giving the foliage a burnt/scorched appearance.",
            "Leaves curl at the edges and die."
        ],
        "organic_remedies": [
            "Copper fungicides applied in early spring when new growth begins.",
            "Mow or renovate strawberry beds immediately after harvest."
        ],
        "chemical_treatments": [
            "Fungicides such as Captan, Thiram, or Pyraclostrobin."
        ],
        "prevention": [
            "Plant disease-free certified runners.",
            "Ensure wide row spacing to promote quick foliage drying."
        ]
    }
}


def download_image_from_url(url: str, dest_folder: str) -> str:
    """
    Downloads an image from a public internet URL and saves it locally.
    Validates protocol, status code, size, and image format.
    """
    url = url.strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme. The image URL must start with http:// or https://.")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 AI-Crop-Detector/1.0"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=12, stream=True)
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Could not connect to internet URL: {str(e)}")

    if response.status_code != 200:
        raise ValueError(f"Failed to fetch image. Server returned HTTP {response.status_code}.")

    # Limit to 15MB
    content = b""
    max_bytes = 15 * 1024 * 1024
    for chunk in response.iter_content(chunk_size=65536):
        content += chunk
        if len(content) > max_bytes:
            raise ValueError("Image file is too large (maximum allowed size is 15MB).")

    try:
        image = Image.open(BytesIO(content))
        image.verify()  # Verify image integrity
        # Re-open for actual processing as verify closes/invalidates the image object
        image = Image.open(BytesIO(content))
    except Exception:
        raise ValueError("The provided internet URL does not point to a valid image.")

    os.makedirs(dest_folder, exist_ok=True)
    ext = image.format.lower() if image.format else "jpg"
    if ext == "jpeg":
        ext = "jpg"

    filename = f"url_{int(time.time())}_{abs(hash(url)) % 100000}.{ext}"
    filepath = os.path.join(dest_folder, filename)
    image.convert("RGB").save(filepath)

    return filepath


def parse_class_name(raw_class: str) -> tuple:
    """
    Splits a dataset class name into clean (Crop, Disease, Key).
    E.g. 'Tomato___Late_blight' -> ('Tomato', 'Late Blight', 'Late_blight')
    """
    if "___" in raw_class:
        crop_part, disease_part = raw_class.split("___", 1)
    else:
        crop_part, disease_part = raw_class, ""

    crop_clean = crop_part.replace("_", " ").strip()
    disease_clean = disease_part.replace("_", " ").strip()

    if not disease_clean:
        disease_clean = "Healthy"

    # Match key in AGRONOMIC_KNOWLEDGE_BASE
    matched_key = None
    for key in AGRONOMIC_KNOWLEDGE_BASE.keys():
        if key.lower() in disease_part.lower():
            matched_key = key
            break

    return crop_clean, disease_clean, matched_key


def fetch_from_gemini(crop_name: str, disease_name: str) -> dict:
    """
    Queries Google Gemini API for real-time agricultural diagnosis,
    symptoms, organic remedies, and chemical controls.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    prompt = (
        f"You are an expert plant pathologist and agronomist. Provide practical, accurate agricultural advice for: "
        f"Crop: {crop_name}, Disease/Condition: {disease_name}.\n"
        "Return ONLY a JSON object with this exact structure:\n"
        "{\n"
        '  "overview": "2-3 sentences explaining the disease and causes.",\n'
        '  "symptoms": ["symptom 1", "symptom 2", "symptom 3"],\n'
        '  "organic_remedies": ["organic remedy 1", "organic remedy 2", "organic remedy 3"],\n'
        '  "chemical_treatments": ["chemical treatment 1", "chemical treatment 2"],\n'
        '  "prevention": ["preventive tip 1", "preventive tip 2", "preventive tip 3"]\n'
        "}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)
            parsed["source"] = "Google Gemini AI (Live Online Intelligence)"
            return parsed
    except Exception as e:
        print(f"Gemini API request failed ({e}), falling back to Wikipedia/agronomic base.")

    return None


def fetch_from_wikipedia(wiki_page_title: str) -> str:
    """
    Fetches real-time summary for the disease from the Wikipedia REST API.
    """
    if not wiki_page_title:
        return None

    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_page_title}"
    headers = {"User-Agent": "AI-Crop-Disease-Detector/1.0 (contact@example.com)"}

    try:
        res = requests.get(api_url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            extract = data.get("extract")
            if extract and len(extract) > 40:
                return extract
    except Exception as e:
        print(f"Wikipedia lookup error for {wiki_page_title}: {e}")

    return None


def fetch_online_disease_info(raw_class_name: str) -> dict:
    """
    Fetches comprehensive agricultural details for a detected crop class.
    Tries:
    1. In-memory cache
    2. Google Gemini AI (if GEMINI_API_KEY configured)
    3. Wikipedia REST API live summary + Curated Agronomic Database
    4. Safe defaults
    """
    if raw_class_name in _DISEASE_CACHE:
        return _DISEASE_CACHE[raw_class_name]

    crop_clean, disease_clean, matched_key = parse_class_name(raw_class_name)
    is_healthy = "healthy" in raw_class_name.lower()

    if is_healthy:
        result = {
            "crop": crop_clean,
            "disease": "Healthy Plant (No Disease Detected)",
            "is_healthy": True,
            "overview": (
                f"The {crop_clean} foliage exhibits healthy leaf characteristics with normal chlorophyll "
                "pigmentation and no signs of bacterial, viral, or fungal infection."
            ),
            "symptoms": [
                "Leaves show standard green coloration and uniform texture.",
                "No necrotic spots, lesions, chlorosis, or wilting detected.",
                "Normal leaf margin and robust vegetative growth."
            ],
            "organic_remedies": [
                "Apply organic compost or well-rotted manure to nourish the root zone.",
                "Use seaweed liquid fertilizer or fish emulsion for micro-nutrient balance.",
                "Incorporate beneficial mycorrhizal fungi to enhance nutrient uptake."
            ],
            "chemical_treatments": [
                "No chemical pesticides or fungicides required.",
                "Maintain balanced N-P-K soil fertilization based on soil testing."
            ],
            "prevention": [
                "Maintain consistent watering at root level without wetting foliage.",
                "Ensure proper crop spacing to maintain air circulation.",
                "Regularly scout leaves to catch any pest or disease signs early."
            ],
            "soil_nutrients": [
                "Test soil pH annually (ideal range: 6.0 - 6.8 for most crops).",
                "Apply balanced N-P-K (10-10-10 or 5-10-10) during active vegetative growth.",
                "Top-dress with aged organic compost (2-3 inches) to maintain soil microbiome."
            ],
            "irrigation": [
                "Utilize drip or soaker irrigation to prevent splashing fungal spores onto leaves.",
                "Irrigate early in the morning so incidental leaf moisture evaporates quickly in sunlight."
            ],
            "source": "Agronomic Plant Health Guide"
        }
        _DISEASE_CACHE[raw_class_name] = result
        return result

    # 1. Try Gemini AI
    gemini_data = fetch_from_gemini(crop_clean, disease_clean)
    if gemini_data and isinstance(gemini_data, dict):
        result = {
            "crop": crop_clean,
            "disease": disease_clean,
            "is_healthy": False,
            "overview": gemini_data.get("overview", ""),
            "symptoms": gemini_data.get("symptoms", []),
            "organic_remedies": gemini_data.get("organic_remedies", []),
            "chemical_treatments": gemini_data.get("chemical_treatments", []),
            "prevention": gemini_data.get("prevention", []),
            "soil_nutrients": gemini_data.get("soil_nutrients", [
                "Avoid high nitrogen fertilizers during active disease outbreaks (excess nitrogen softens tissue).",
                "Supplement calcium (calcium nitrate or gypsum) and potassium to strengthen plant cell walls."
            ]),
            "irrigation": gemini_data.get("irrigation", [
                "Immediately cease overhead sprinkler watering; convert to drip or ground-level irrigation.",
                "Allow the top 1-2 inches of soil to dry out between waterings to reduce ambient humidity."
            ]),
            "source": gemini_data.get("source", "Google Gemini AI (Live Online Intelligence)")
        }
        _DISEASE_CACHE[raw_class_name] = result
        return result

    # 2. Try Wikipedia Live API + Curated Knowledge Base
    base_data = AGRONOMIC_KNOWLEDGE_BASE.get(matched_key, {})
    wiki_title = base_data.get("wiki_page", disease_clean.replace(" ", "_"))
    live_wiki_summary = fetch_from_wikipedia(wiki_title)

    overview = live_wiki_summary or base_data.get(
        "overview",
        f"{disease_clean} is a known crop disorder impacting {crop_clean}. Early detection and proactive treatment are critical to safeguard yield."
    )

    source = (
        "Wikipedia REST API (Live Online) & Agronomic Guide"
        if live_wiki_summary
        else "Curated Agronomic Disease Knowledge Base"
    )

    symptoms = base_data.get("symptoms", [
        f"Observable lesions, spots, or abnormal discoloration on {crop_clean} leaves.",
        "Reduction in photosynthetic leaf surface and stunted vigor.",
        "Premature foliage drop or yellowing."
    ])

    organic_remedies = base_data.get("organic_remedies", [
        "Spray organic copper or sulfur-based protectants.",
        "Apply neem oil extract or biological control agents (e.g., Bacillus subtilis).",
        "Prune and destroy infected leaves to halt spore propagation."
    ])

    chemical_treatments = base_data.get("chemical_treatments", [
        "Consult local agricultural extension service for registered broad-spectrum fungicides.",
        "Apply protectant sprays (e.g., Mancozeb or Chlorothalonil) adhering strictly to label instructions."
    ])

    prevention = base_data.get("prevention", [
        "Ensure optimal plant spacing for thorough airflow and rapid leaf drying.",
        "Utilize drip irrigation to avoid wet foliage.",
        "Practice crop rotation with non-host species."
    ])

    soil_nutrients = [
        "Avoid excess nitrogen fertilizer which creates succulent, disease-prone leaf growth.",
        "Apply potassium and silica supplements to enhance cuticle thickness and defense resistance.",
        "Maintain soil organic matter above 3% with well-composted organic material."
    ]

    irrigation = [
        "Avoid overhead sprinkler irrigation; always irrigate directly at the root zone.",
        "Water early in the morning so foliage dries quickly under daylight.",
        "Ensure proper soil drainage to prevent root waterlogging and fungal sporulation."
    ]

    result = {
        "crop": crop_clean,
        "disease": disease_clean,
        "is_healthy": False,
        "overview": overview,
        "symptoms": symptoms,
        "organic_remedies": organic_remedies,
        "chemical_treatments": chemical_treatments,
        "prevention": prevention,
        "soil_nutrients": soil_nutrients,
        "irrigation": irrigation,
        "source": source
    }

    _DISEASE_CACHE[raw_class_name] = result
    return result

