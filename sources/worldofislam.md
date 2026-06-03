# WorldOfIslam — E-number Halal Status List

Source URL:    https://special.worldofislam.info/Food/numbers.html
Source type:   community  (not a certification authority)
Last extracted: 2026-06-03 by `scripts/extract_worldofislam.py`

The bootstrap pipeline merges these opinions into `data/ingredients.json`
as additional rows in each ingredient's `rulings.halal.opinions[]`.
Each row carries `type: "community"` and a `ref` URL back to this page.

Status legend (left column maps to our schema's effective_status):

  halal      -> allowed
  haram      -> forbidden
  mushbooh   -> caution
  halal_or_haram -> caution (source-dependent; conservative = caution)

| E-number | Name                                  | Status         | Reasoning                                              |
|----------|---------------------------------------|----------------|--------------------------------------------------------|
| E100     | Curcumin / Turmeric                   | mushbooh       | Depends on form and solvents used                      |
| E101     | Riboflavin (Vitamin B2)               | mushbooh       | Haram if derived from pork liver/kidney                |
| E102     | Tartrazine                            | halal          | If 100% dry color                                      |
| E104     | Quinoline Yellow                      | halal          | If 100% dry color                                      |
| E110     | Sunset Yellow FCF                     | halal          | If 100% dry color                                      |
| E120     | Cochineal / Carminic Acid             | haram          | Insect-derived                                         |
| E122     | Carmoisine / Azorubine                | halal          | If 100% dry color                                      |
| E123     | Amaranth                              | halal          | If 100% dry color                                      |
| E124     | Ponceau 4R                            | halal          | If 100% dry color                                      |
| E127     | Erythrosine BS                        | halal          | If 100% dry color                                      |
| E131     | Patent Blue V                         | halal          | If 100% dry color                                      |
| E132     | Indigo Carmine                        | halal          | Unless pork glycerin added as solvent                  |
| E140     | Chlorophyll                           | halal          | If 100% powder or halal solvents                       |
| E141     | Copper Complex of Chlorophyll         | halal          | If 100% powder or halal solvents                       |
| E142     | Green S                               | halal          | If 100% dry color                                      |
| E150     | Caramel Color (a-d)                   | halal          | All variants acceptable                                |
| E151     | Black PN                              | halal          | If 100% dry color                                      |
| E153     | Carbon Black / Vegetable Carbon       | halal          | If 100% dry color                                      |
| E160a    | Alpha / Beta / Gamma Carotene         | halal          | If 100% dry color                                      |
| E160b    | Annatto, Bixin, Norbixin              | halal          | All forms acceptable                                   |
| E160c    | Capsanthin / Capsorbin                | halal          | If 100% dry color                                      |
| E160d    | Lycopene                              | halal          | If 100% dry color                                      |
| E160e    | Beta-apo-8-carotenal                  | halal          | If dry powder or vegetable oil solvent                 |
| E160f    | Ethyl ester of Beta-apo-8-carotenal   | halal          | If dry powder or vegetable oil solvent                 |
| E161a    | Flavoxanthin                          | halal          | If 100% dry color                                      |
| E161b    | Lutein                                | halal          | Unless pork gelatin/glycerin added                     |
| E161c    | Cryptoxanthin                         | halal          | If 100% dry color                                      |
| E161d    | Rubixanthin                           | halal          | If 100% dry color                                      |
| E161e    | Violaxanthin                          | halal          | If 100% dry color                                      |
| E161f    | Rhodoxanthin                          | halal          | If 100% dry color                                      |
| E161g    | Canthaxanthin                         | halal          | If 100% dry color                                      |
| E162     | Beetroot Red / Betanin                | halal          | If 100% dry color                                      |
| E163     | Anthocyanins                          | halal          | If 100% dry color                                      |
| E170     | Calcium Carbonate                     | halal          | If from rock mineral                                   |
| E171     | Titanium Dioxide                      | halal          | Universally acceptable                                 |
| E172     | Iron Oxides and Hydroxides            | halal          | Universally acceptable                                 |
| E173     | Aluminium                             | halal          | Universally acceptable                                 |
| E174     | Silver                                | halal          | Universally acceptable                                 |
| E175     | Gold                                  | halal          | Universally acceptable                                 |
| E180     | Pigment Rubine                        | halal          | If 100% dry color                                      |
| E200     | Sorbic Acid                           | halal          | Universally acceptable                                 |
| E201     | Sodium Sorbate                        | halal          | Universally acceptable                                 |
| E202     | Potassium Sorbate                     | halal          | Universally acceptable                                 |
| E203     | Calcium Sorbate                       | halal          | Universally acceptable                                 |
| E210     | Benzoic Acid                          | halal          | Universally acceptable                                 |
| E211     | Sodium Benzoate                       | halal          | Universally acceptable                                 |
| E212     | Potassium Benzoate                    | halal          | Universally acceptable                                 |
| E213     | Calcium Benzoate                      | halal          | If mineral calcium                                     |
| E214     | Ethyl 4-hydroxybenzoate               | halal          | Unless alcohol used as solvent                         |
| E215     | Ethyl 4-hydroxybenzoate, Sodium Salt  | halal          | Unless alcohol used as solvent                         |
| E216     | Propyl 4-hydroxybenzoate              | halal          | Unless alcohol used as solvent                         |
| E217     | Propyl 4-hydroxybenzoate, Sodium Salt | halal          | Unless alcohol used as solvent                         |
| E218     | Methyl 4-hydroxybenzoate              | halal          | Unless alcohol used as solvent                         |
| E219     | Methyl 4-hydroxybenzoate, Sodium Salt | halal          | Unless alcohol used as solvent                         |
| E220     | Sulfur Dioxide                        | halal          | Universally acceptable                                 |
| E221     | Sodium Sulfite                        | halal          | Universally acceptable                                 |
| E222     | Sodium Hydrogen Sulfite               | halal          | Universally acceptable                                 |
| E223     | Sodium Metabisulfite                  | halal          | Universally acceptable                                 |
| E224     | Potassium Metabisulfite               | halal          | Universally acceptable                                 |
| E226     | Calcium Sulfite                       | halal          | Universally acceptable                                 |
| E227     | Calcium Hydrogen Sulfite              | halal          | If mineral calcium                                     |
| E230     | Biphenyl / Diphenyl                   | halal          | If no alcohol used as solvent                          |
| E231     | 2-Hydroxybiphenyl                     | halal          | If no alcohol used as solvent                          |
| E232     | Sodium Biphenyl-2-yl Oxide            | halal          | If no alcohol used as solvent                          |
| E233     | 2-(Thiazol-4-yl) Benzimidazole        | halal          | If no alcohol used as solvent                          |
| E239     | Hexamine                              | halal          | Universally acceptable                                 |
| E249     | Potassium Nitrite                     | halal          | Universally acceptable                                 |
| E250     | Sodium Nitrite                        | halal          | Universally acceptable                                 |
| E251     | Sodium Nitrate                        | halal          | Universally acceptable                                 |
| E252     | Potassium Nitrate (Saltpetre)         | halal          | Universally acceptable                                 |
| E260     | Acetic Acid                           | halal          | Universally acceptable                                 |
| E261     | Potassium Acetate                     | halal          | Universally acceptable                                 |
| E262     | Potassium Hydrogen Diacetate          | halal          | Universally acceptable                                 |
| E263     | Calcium Acetate                       | halal          | Universally acceptable                                 |
| E270     | Lactic Acid                           | halal          | If from non-dairy source                               |
| E280     | Propionic Acid                        | halal          | Universally acceptable                                 |
| E281     | Sodium Propionate                     | halal          | Universally acceptable                                 |
| E282     | Calcium Propionate                    | halal          | If mineral calcium                                     |
| E283     | Potassium Propionate                  | halal          | Universally acceptable                                 |
| E290     | Carbon Dioxide                        | halal          | Universally acceptable                                 |
| E300     | L-Ascorbic Acid (Vitamin C)           | halal          | Universally acceptable                                 |
| E301     | Sodium-L-Ascorbate                    | halal          | Universally acceptable                                 |
| E302     | Calcium-L-Ascorbate                   | halal          | If mineral calcium                                     |
| E304     | Ascorbyl Palmitate                    | halal_or_haram | Halal if plant-derived fatty acid; haram if pork       |
| E306     | Natural Extracts rich in Tocopherols  | halal_or_haram | Halal if plant fat; haram if pork fat                  |
| E307     | Synthetic Alpha-Tocopherol            | halal          | If all halal synthetic material                        |
| E308     | Synthetic Gamma-Tocopherol            | halal          | If all halal synthetic material                        |
| E309     | Synthetic Delta-Tocopherol            | halal          | If all halal synthetic material                        |
| E310     | Propyl Gallate                        | halal          | Universally acceptable                                 |
| E311     | Octyl Gallate                         | halal          | If from nutgalls or plant secretion                    |
| E312     | Dodecyl Gallate                       | halal          | Unless alcohol used as solvent                         |
| E320     | Butylated Hydroxyanisole (BHA)        | halal_or_haram | Halal if vegetable oil carrier; haram if pork          |
| E321     | Butylated Hydroxytoluene (BHT)        | halal_or_haram | Halal if vegetable oil carrier; haram if pork          |
| E322     | Lecithin                              | halal          | If from soy or egg yolk                                |
| E325     | Sodium Lactate                        | halal          | If from non-dairy source                               |
| E326     | Potassium Lactate                     | halal          | If from non-dairy source                               |
| E327     | Calcium Lactate                       | halal          | If non-dairy and mineral calcium                       |
| E330     | Citric Acid                           | halal          | Universally acceptable                                 |
| E331     | Sodium Citrates                       | halal          | Universally acceptable                                 |
| E332     | Potassium Citrates                    | halal          | Universally acceptable                                 |
| E333     | Calcium Citrates                      | halal          | If not from bones                                      |
| E334     | Tartaric Acid                         | halal          | If not from wine by-product                            |
| E335     | Sodium Tartrates                      | halal          | If not from wine by-product                            |
| E336     | Potassium Tartrates (Cream of Tartar) | halal          | If not from wine by-product                            |
| E337     | Potassium Sodium Tartrates            | halal          | If not from wine by-product                            |
| E338     | Orthophosphoric Acid                  | halal          | Universally acceptable                                 |
| E339     | Sodium Phosphates                     | halal          | Universally acceptable                                 |
| E340     | Potassium Phosphates                  | halal          | Universally acceptable                                 |
| E341     | Calcium Phosphates                    | halal          | If mineral calcium source                              |
| E400     | Alginic Acid                          | halal          | Universally acceptable                                 |
| E401     | Sodium Alginate                       | halal          | Universally acceptable                                 |
| E402     | Potassium Alginate                    | halal          | Universally acceptable                                 |
| E403     | Ammonium Alginate                     | halal          | Universally acceptable                                 |
| E404     | Calcium Alginate                      | halal          | If mineral calcium source                              |
| E405     | Propane-1,2-Diol Alginate             | halal          | Universally acceptable                                 |
| E406     | Agar                                  | halal          | Universally acceptable                                 |
| E407     | Carrageenan                           | halal          | Universally acceptable                                 |
| E410     | Locust Bean Gum (Carob Gum)           | halal          | Universally acceptable                                 |
| E412     | Guar Gum                              | halal          | Universally acceptable                                 |
| E413     | Tragacanth                            | halal          | Universally acceptable                                 |
| E414     | Gum Acacia (Gum Arabic)               | halal          | Universally acceptable                                 |
| E415     | Xanthan Gum                           | halal          | Universally acceptable                                 |
| E420     | Sorbitol                              | halal          | Universally acceptable                                 |
| E421     | Mannitol                              | halal          | Universally acceptable                                 |
| E422     | Glycerol                              | mushbooh       | Haram if from pork fat                                 |
| E440     | Pectin / Amidated Pectin              | halal          | Universally acceptable                                 |
| E450     | Sodium / Potassium Phosphates         | halal          | Universally acceptable                                 |
| E460     | Microcrystalline / Powdered Cellulose | halal          | Universally acceptable                                 |
| E461     | Methylcellulose                       | halal          | Universally acceptable                                 |
| E463     | Hydroxypropylcellulose                | halal          | Universally acceptable                                 |
| E464     | Hydroxypropyl-Methylcellulose         | halal          | Universally acceptable                                 |
| E465     | Ethylmethylcellulose                  | halal          | Universally acceptable                                 |
| E466     | Carboxymethylcellulose, Sodium Salt   | halal          | Universally acceptable                                 |
| E470     | Sodium / Potassium / Calcium Fatty-Acid Salts | mushbooh | Haram if from pork fat                                 |
| E471     | Mono- and Diglycerides of Fatty Acids | mushbooh       | Haram if from pork fat                                 |
| E472     | Esters of Mono- and Diglycerides      | mushbooh       | Haram if from pork fat                                 |
| E473     | Sucrose Esters of Fatty Acids         | mushbooh       | Haram if from pork fat                                 |
| E474     | Sucroglycerides                       | mushbooh       | Haram if from pork fat                                 |
| E475     | Polyglycerol Esters of Fatty Acids    | mushbooh       | Haram if from pork fat                                 |
| E477     | Propane-1,2-Diol Esters of Fatty Acids| mushbooh       | Haram if from pork fat                                 |
| E481     | Sodium Stearoyl-2-Lactylate           | mushbooh       | Haram if from pork fat                                 |
| E482     | Calcium Stearoyl-2-Lactylate          | mushbooh       | Haram if from pork fat                                 |
| E483     | Stearyl Tartrate                      | mushbooh       | Haram if from pork fat                                 |
| E500     | Sodium Carbonate / Bicarbonate        | halal          | Universally acceptable                                 |
| E501     | Potassium Carbonate / Bicarbonate     | halal          | Universally acceptable                                 |
| E503     | Ammonium Carbonate                    | halal          | Universally acceptable                                 |
| E504     | Magnesium Carbonate                   | halal          | Universally acceptable                                 |
| E507     | Hydrochloric Acid                     | halal          | Universally acceptable                                 |
| E508     | Potassium Chloride                    | halal          | Universally acceptable                                 |
| E509     | Calcium Chloride                      | halal          | Universally acceptable                                 |
| E510     | Ammonium Chloride                     | halal          | Universally acceptable                                 |
| E513     | Sulfuric Acid                         | halal          | Universally acceptable                                 |
| E514     | Sodium Sulfate                        | halal          | Universally acceptable                                 |
| E515     | Potassium Sulfate                     | halal          | Universally acceptable                                 |
| E516     | Calcium Sulfate                       | halal          | Universally acceptable                                 |
| E518     | Magnesium Sulfate                     | halal          | Universally acceptable                                 |
| E524     | Sodium Hydroxide                      | halal          | Universally acceptable                                 |
| E525     | Potassium Hydroxide                   | halal          | Universally acceptable                                 |
| E526     | Calcium Hydroxide                     | halal          | Universally acceptable                                 |
| E527     | Ammonium Hydroxide                    | halal          | Universally acceptable                                 |
| E528     | Magnesium Hydroxide                   | halal          | Universally acceptable                                 |
| E529     | Calcium Oxide                         | halal          | Universally acceptable                                 |
| E530     | Magnesium Oxide                       | halal          | Universally acceptable                                 |
| E535     | Sodium Ferrocyanide                   | halal          | Universally acceptable                                 |
| E536     | Potassium Ferrocyanide                | halal          | Universally acceptable                                 |
| E540     | Dicalcium Ferrocyanide                | halal          | Universally acceptable                                 |
| E541     | Sodium Aluminium Phosphate            | halal          | Universally acceptable                                 |
| E542     | Edible Bone Phosphate (Bone-Meal)     | haram          | If bones from pig                                      |
| E544     | Calcium Polyphosphates                | mushbooh       | Haram if from pig bones                                |
| E545     | Ammonium Polyphosphates               | halal          | Universally acceptable                                 |
| E551     | Silicon Dioxide                       | halal          | Universally acceptable                                 |
| E552     | Calcium Silicate                      | halal          | Universally acceptable                                 |
| E553     | Magnesium Silicate / Talc             | halal          | Universally acceptable                                 |
| E554     | Aluminium Sodium Silicate             | halal          | Universally acceptable                                 |
| E556     | Aluminium Calcium Silicate            | mushbooh       | Haram if calcium from pig bones                        |
| E558     | Bentonite                             | halal          | Universally acceptable                                 |
| E559     | Kaolin (Aluminium Silicate)           | halal          | Universally acceptable                                 |
| E570     | Stearic Acid                          | mushbooh       | Haram if from pork fat                                 |
| E572     | Magnesium Stearate                    | mushbooh       | Haram if from pork fat                                 |
| E575     | Glucono Delta-Lactone                 | halal          | Universally acceptable                                 |
| E576     | Sodium Gluconate                      | halal          | Universally acceptable                                 |
| E577     | Potassium Gluconate                   | halal          | Universally acceptable                                 |
| E578     | Calcium Gluconate                     | halal          | Universally acceptable                                 |
| E620     | L-Glutamic Acid                       | mushbooh       | Haram if from pig protein                              |
| E621     | Monosodium Glutamate (MSG)            | mushbooh       | Haram if culture media from pork fat                   |
| E622     | Monopotassium Glutamate               | mushbooh       | Haram if culture media from pork fat                   |
| E623     | Calcium Glutamate                     | mushbooh       | Haram if culture media from pork fat                   |
| E627     | Sodium Guanylate                      | halal          | If from sardines or baker's yeast                      |
| E631     | Sodium Inosinate                      | halal          | If from sardines                                       |
| E636     | Maltol                                | halal          | Universally acceptable                                 |
| E637     | Ethyl Maltol                          | halal          | Universally acceptable                                 |
| E900     | Dimethylpolysiloxane                  | halal          | Universally acceptable                                 |
| E901     | Beeswax                               | halal          | Universally acceptable                                 |
| E903     | Carnauba Wax                          | halal          | Universally acceptable                                 |
| E904     | Shellac                               | halal          | Unless treated with alcohol                            |
| E905     | Mineral Hydrocarbons                  | halal          | Universally acceptable                                 |
| E907     | Refined Microcrystalline Wax          | mushbooh       | Haram if from pork fat wax                             |
| E920     | L-Cysteine Hydrochloride              | mushbooh       | Contentious sources; opinions vary                     |
| E924     | Potassium Bromate                     | halal          | Universally acceptable                                 |
| E925     | Chlorine                              | halal          | Universally acceptable                                 |
| E926     | Chlorine Dioxide                      | halal          | Universally acceptable                                 |
| E927     | Azodicarbonamide                      | halal          | Universally acceptable                                 |
