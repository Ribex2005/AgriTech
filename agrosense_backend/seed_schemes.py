from datetime import datetime
from api.mongo_client import get_db

def seed_schemes():
    db = get_db()

    schemes = [
        {
            "scheme_id": "PMFBY",
            "title": "Pradhan Mantri Fasal Bima Yojana",
            "category": "Insurance",
            "description": "Crop insurance scheme protecting farmers against yield loss.",
            "benefits": [
                "Insurance coverage for crop loss",
                "Subsidized premium rates",
                "Applicable to loanee and non-loanee farmers"
            ],
            "eligible_crops": ["wheat", "rice", "maize", "all"],
            "eligible_states": ["All"],
            "farmer_type": ["all"],
            "official_link": "https://pmfby.gov.in",
            "is_flagship": True,
            "last_updated": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
                {
            "scheme_id": "PMKSY",
            "title": "Pradhan Mantri Krishi Sinchayee Yojana",
            "category": "Irrigation",
            "description": "Improves irrigation coverage and water use efficiency.",
            "benefits": [
                "Financial support for irrigation",
                "Micro irrigation promotion",
                "Water conservation support"
            ],
            "eligible_crops": ["all"],
            "eligible_states": ["All"],
            "farmer_type": ["all"],
            "official_link": "https://pmksy.gov.in",
            "is_flagship": True,
            "last_updated": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
            "scheme_id": "SOILHC",
            "title": "Soil Health Card Scheme",
            "category": "Soil Health",
            "description": "Provides soil health cards to farmers with crop-wise recommendations.",
            "benefits": [
                "Soil nutrient analysis",
                "Crop-specific fertilizer guidance"
            ],
            "eligible_crops": ["all"],
            "eligible_states": ["All"],
            "farmer_type": ["all"],
            "official_link": "https://soilhealth.dac.gov.in",
            "is_flagship": False,
            "last_updated": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
            "scheme_id": "KCC",
            "title": "Kisan Credit Card Scheme",
            "category": "Credit",
            "description": "Provides short-term credit support to farmers.",
            "benefits": [
                "Low interest agricultural loans",
                "Flexible repayment options"
            ],
            "eligible_crops": ["all"],
            "eligible_states": ["All"],
            "farmer_type": ["all"],
            "official_link": "https://pmkisan.gov.in/Kcc.aspx",
            "is_flagship": False,
            "last_updated": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
    "scheme_id": "WBCIS",
    "title": "Weather Based Crop Insurance Scheme",
    "category": "Insurance",
    "description": "Provides insurance protection against adverse weather conditions.",
    "benefits": [
        "Weather-based risk coverage",
        "Quick claim settlement",
        "Reduced financial loss due to climate risk"
    ],
    "eligible_crops": ["wheat", "rice", "maize", "all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://pmfby.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "CPIS",
    "title": "Coconut Palm Insurance Scheme",
    "category": "Insurance",
    "description": "Insurance scheme for coconut farmers against natural calamities.",
    "benefits": [
        "Compensation for damaged coconut palms",
        "Low premium rates"
    ],
    "eligible_crops": ["coconut"],
    "eligible_states": ["Kerala", "Tamil Nadu", "Karnataka"],
    "farmer_type": ["all"],
    "official_link": "https://coconutboard.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "LIVESTOCK_INS",
    "title": "Livestock Insurance Scheme",
    "category": "Insurance",
    "description": "Insurance coverage for livestock against death due to disease or accident.",
    "benefits": [
        "Coverage for cattle loss",
        "Subsidized premium"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://dahd.nic.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "UPIS",
    "title": "Unified Package Insurance Scheme",
    "category": "Insurance",
    "description": "Comprehensive insurance coverage for crops, assets, and life.",
    "benefits": [
        "Crop insurance",
        "Asset insurance",
        "Life insurance component"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://pmfby.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "AIF",
    "title": "Agricultural Infrastructure Fund",
    "category": "Credit",
    "description": "Provides medium to long term debt financing for agricultural infrastructure projects.",
    "benefits": [
        "Interest subvention",
        "Credit guarantee support"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://agriinfra.dac.gov.in",
    "is_flagship": True,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "RIDF",
    "title": "NABARD Rural Infrastructure Development Fund",
    "category": "Credit",
    "description": "Supports rural infrastructure including irrigation and agriculture.",
    "benefits": [
        "Financial assistance for rural projects",
        "Infrastructure development"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://nabard.org",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "DEDS",
    "title": "Dairy Entrepreneurship Development Scheme",
    "category": "Credit",
    "description": "Provides financial assistance for dairy farming enterprises.",
    "benefits": [
        "Subsidy for dairy units",
        "Loan support for dairy farmers"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["small", "marginal"],
    "official_link": "https://nabard.org",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "STANDUP_INDIA",
    "title": "Stand-Up India Scheme",
    "category": "Credit",
    "description": "Provides loans to SC/ST and women entrepreneurs including agri ventures.",
    "benefits": [
        "Bank loans for agri-enterprises",
        "Support for entrepreneurship"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://standupmitra.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "MUDRA",
    "title": "Pradhan Mantri Mudra Yojana",
    "category": "Credit",
    "description": "Provides micro-financing support for agricultural and allied activities.",
    "benefits": [
        "Collateral-free loans",
        "Support for agri startups"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://mudra.org.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "MIF",
    "title": "Micro Irrigation Fund",
    "category": "Irrigation",
    "description": "Supports micro irrigation systems like drip and sprinkler irrigation.",
    "benefits": [
        "Financial support for drip irrigation",
        "Improves water efficiency",
        "Promotes sustainable farming"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://nabard.org",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "PER_DROP",
    "title": "Per Drop More Crop",
    "category": "Irrigation",
    "description": "Promotes water use efficiency at farm level.",
    "benefits": [
        "Subsidy for micro irrigation",
        "Water conservation support"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://pmksy.gov.in",
    "is_flagship": True,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "ATAL_BHUJAL",
    "title": "Atal Bhujal Yojana",
    "category": "Irrigation",
    "description": "Promotes sustainable groundwater management.",
    "benefits": [
        "Groundwater recharge initiatives",
        "Community-based water management"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["Gujarat", "Haryana", "Karnataka", "Madhya Pradesh", "Maharashtra", "Rajasthan", "Uttar Pradesh"],
    "farmer_type": ["all"],
    "official_link": "https://jalshakti-dowr.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "WATERSHED",
    "title": "Watershed Development Component",
    "category": "Irrigation",
    "description": "Supports watershed development and soil conservation.",
    "benefits": [
        "Improves soil moisture",
        "Reduces land degradation"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://pmksy.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "NFSM",
    "title": "National Food Security Mission",
    "category": "Subsidy",
    "description": "Increases production of rice, wheat, pulses and coarse cereals.",
    "benefits": [
        "Subsidized seeds",
        "Fertilizer support",
        "Farm machinery assistance"
    ],
    "eligible_crops": ["wheat", "rice", "pulses", "maize"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://nfsm.gov.in",
    "is_flagship": True,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "PKVY",
    "title": "Paramparagat Krishi Vikas Yojana",
    "category": "Subsidy",
    "description": "Promotes organic farming and cluster-based organic cultivation.",
    "benefits": [
        "Financial support for organic inputs",
        "Training support",
        "Certification assistance"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["small", "marginal", "all"],
    "official_link": "https://pgsindia-ncof.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "SMAM",
    "title": "Sub-Mission on Agricultural Mechanization",
    "category": "Subsidy",
    "description": "Provides subsidy for purchasing farm machinery.",
    "benefits": [
        "Subsidy for tractors and implements",
        "Promotes mechanized farming"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://agrimachinery.nic.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "UREA_SUB",
    "title": "Neem Coated Urea Subsidy Scheme",
    "category": "Subsidy",
    "description": "Provides subsidized neem-coated urea to improve fertilizer efficiency.",
    "benefits": [
        "Reduces nitrogen loss",
        "Improves crop yield"
    ],
    "eligible_crops": ["wheat", "rice", "all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://fert.nic.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "MIDH",
    "title": "Mission for Integrated Development of Horticulture",
    "category": "Subsidy",
    "description": "Promotes holistic growth of horticulture sector.",
    "benefits": [
        "Financial support for horticulture crops",
        "Infrastructure assistance"
    ],
    "eligible_crops": ["fruits", "vegetables", "all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://midh.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "UK_ORGANIC",
    "title": "Uttarakhand Organic Farming Promotion Scheme",
    "category": "Subsidy",
    "description": "Promotes organic farming practices in Uttarakhand.",
    "benefits": [
        "Financial support for organic inputs",
        "Training and certification assistance"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["Uttarakhand"],
    "farmer_type": ["all"],
    "official_link": "https://uk.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "UP_YANTRA",
    "title": "Uttar Pradesh Krishi Yantra Subsidy Scheme",
    "category": "Subsidy",
    "description": "Provides subsidy on agricultural machinery in Uttar Pradesh.",
    "benefits": [
        "Machinery purchase subsidy",
        "Improved farm productivity"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["Uttar Pradesh"],
    "farmer_type": ["all"],
    "official_link": "https://up.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "PB_DIVERSIFY",
    "title": "Punjab Crop Diversification Scheme",
    "category": "Subsidy",
    "description": "Encourages farmers to diversify crops beyond wheat and rice.",
    "benefits": [
        "Financial incentives",
        "Support for alternative crops"
    ],
    "eligible_crops": ["maize", "pulses"],
    "eligible_states": ["Punjab"],
    "farmer_type": ["all"],
    "official_link": "https://punjab.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "MH_DRIP",
    "title": "Maharashtra Drip Irrigation Subsidy Scheme",
    "category": "Irrigation",
    "description": "Subsidy support for drip irrigation systems in Maharashtra.",
    "benefits": [
        "Subsidy for drip systems",
        "Improved water efficiency"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["Maharashtra"],
    "farmer_type": ["all"],
    "official_link": "https://maharashtra.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "TN_PRECISION",
    "title": "Tamil Nadu Precision Farming Scheme",
    "category": "Subsidy",
    "description": "Supports precision farming technologies in Tamil Nadu.",
    "benefits": [
        "Subsidy for precision farming equipment",
        "Training for modern techniques"
    ],
    "eligible_crops": ["vegetables", "fruits"],
    "eligible_states": ["Tamil Nadu"],
    "farmer_type": ["all"],
    "official_link": "https://tn.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "RKVY",
    "title": "Rashtriya Krishi Vikas Yojana",
    "category": "Subsidy",
    "description": "Supports holistic development of agriculture and allied sectors.",
    "benefits": [
        "Financial assistance to states",
        "Infrastructure and innovation support"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://rkvy.nic.in",
    "is_flagship": True,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "NMOOP",
    "title": "National Mission on Oilseeds and Oil Palm",
    "category": "Subsidy",
    "description": "Promotes oilseed production and reduces import dependency.",
    "benefits": [
        "Seed distribution support",
        "Financial incentives"
    ],
    "eligible_crops": ["oilseeds"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://nfsm.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "BLUE_REV",
    "title": "Blue Revolution Scheme",
    "category": "Subsidy",
    "description": "Supports fisheries development and aquaculture.",
    "benefits": [
        "Financial support for fish farming",
        "Infrastructure assistance"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://dof.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "NBM",
    "title": "National Bamboo Mission",
    "category": "Subsidy",
    "description": "Promotes bamboo cultivation and marketing.",
    "benefits": [
        "Plantation support",
        "Market linkage assistance"
    ],
    "eligible_crops": ["bamboo"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://nbm.nic.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "PM_AASHA",
    "title": "Pradhan Mantri Annadata Aay Sanrakshan Abhiyan",
    "category": "Income Support",
    "description": "Ensures remunerative prices for farmers' produce.",
    "benefits": [
        "Price deficiency payments",
        "Procurement support"
    ],
    "eligible_crops": ["pulses", "oilseeds"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://agricoop.nic.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "NBHM",
    "title": "National Beekeeping and Honey Mission",
    "category": "Subsidy",
    "description": "Promotes beekeeping as an allied agricultural activity.",
    "benefits": [
        "Subsidy for beekeeping equipment",
        "Training support"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://nbhm.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
},
{
    "scheme_id": "ACABC",
    "title": "Agri-Clinics and Agri-Business Centres Scheme",
    "category": "Credit",
    "description": "Encourages agri-entrepreneurs to establish agri-business ventures.",
    "benefits": [
        "Training for agri graduates",
        "Loan assistance"
    ],
    "eligible_crops": ["all"],
    "eligible_states": ["All"],
    "farmer_type": ["all"],
    "official_link": "https://acabc.gov.in",
    "is_flagship": False,
    "last_updated": datetime.utcnow(),
    "created_at": datetime.utcnow()
}
    ]

    # Prevent duplicate insertion
    for scheme in schemes:
        existing = db.govt_schemes.find_one({"scheme_id": scheme["scheme_id"]})
        if not existing:
            db.govt_schemes.insert_one(scheme)
            print(f"Inserted {scheme['title']}")
        else:
            print(f"{scheme['title']} already exists")

if __name__ == "__main__":
    seed_schemes()
