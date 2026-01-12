const gmail_process = {
    "login": [

        {"action": "check_if_exist", "xpath":"//a[starts-with(@href,'https://accounts.google.com/AccountChooser')] | //input[@id='identifierId'] | //div[@id='gbwa'] | //div[@id='main-message']", "wait": 6, "sleep": 0,
            //div[@id='gbwa']  deja connecter sur boi de reception 
            "sub_action": [
                {"action": "check_if_exist", "xpath":"//a[starts-with(@href,'https://accounts.google.com/AccountChooser')]", "wait": 3, "sleep": 0,
                    "sub_action": [
                        {"action": "click", "xpath": "//a[starts-with(@href,'https://accounts.google.com/AccountChooser')]", "sleep": 0, "wait": 1}
                    ]
                }, 
                
                {"action": "check_if_exist", "xpath": "//input[@id='identifierId']", "wait": 3,"sleep": 0,
                    "sub_action": [
                        {"action": "send_keys", "xpath": "//input[@id='identifierId']", "value": "__email__" , "wait": 1, "sleep": 1},
                        {"id":1,"action": "press_keys", "xpath": "//button[.//span[text()='Suivant']] | //button[.//span[text()='Next']]", "wait": 1, "sleep": 5 ,
                            "sub_action": [

                                {"action": "check_if_exist", "xpath": "(//a[@aria-label='Try to restore' or @aria-label='Essayer de restaurer'])  | //div[span and (text()[contains(., 'Impossible de trouver votre compte Google')] or .//font[contains(text(), 'Unable to find your Google account')])]", "wait": 4,"sleep": 0,
                                     "sub_action":[
                                        {"action": "check_if_exist", "xpath": "//a[@aria-label='Try to restore' or @aria-label='Essayer de restaurer']", "wait": 2,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist", "xpath": "//a[@aria-label='Try to restore' or @aria-label='Essayer de restaurer']", "wait": 1, "sleep": 0 ,   "obligatoire":true , "type":"restore_account"},   // restore account 
                                            ]
                                        }
                                        , 
                                        // {"action": "check_if_exist", "xpath": "//form//div[contains(text(), 'robot')]", "wait": 4,"sleep": 0, 
                                        //     "sub_action": [
                                        //         {"action": "check_if_exist", "xpath": "//form//div[contains(text(), 'robot')]", "wait": 2, "sleep": 2 },   // validation capcha 
                                        //     ]
                                        // },
                                        {"action": "check_if_exist", "xpath":   "//div[span and (text()[contains(., 'Impossible de trouver votre compte Google')] or .//font[contains(text(), 'Unable to find your Google account')])]", "wait": 4,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist",  "xpath": "//div[span and (text()[contains(., 'Impossible de trouver votre compte Google')] or .//font[contains(text(), 'Unable to find your Google account')])]","wait": 2, "sleep": 2 , "obligatoire":true , "type":"others"},   // others
                                            ]
                                        }

                                    ]
                                }
                                                      
                            ]
                        },
                        {"action": "send_keys", "xpath": "//input[@type='password']", "value":"__password__", "wait": 600000 , "sleep": 1},
                        {"action": "press_keys", "xpath": "//button[.//span[text()='Suivant']] | //button[.//span[text()='Next']]",  "wait": 3, "sleep": 3 ,
                            "sub_action": [

                                {"action": "check_if_exist", "xpath": "//div[@aria-live='polite']//div[@aria-hidden='true']/following-sibling::div//span | (//a[(text()='En savoir plus' or  text()='Learn more')]) | //input[@id='knowledgePreregisteredEmailInput'] | //input[@type='tel' and @pattern='[0-9 ]*'] | //input[@type='tel' and @id='phoneNumberId'] | //button[span[contains(text(), 'Télécharger vos données') or contains(text(), 'Download your data')]]", "wait": 4,"sleep": 0, 

                                    "sub_action": [
                                        {"action": "check_if_exist", "xpath": "//div[@aria-live='polite']//div[@aria-hidden='true']/following-sibling::div//span", "wait": 3,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist", "xpath": "//div[@aria-live='polite']//div[@aria-hidden='true']/following-sibling::div//span", "wait": 2, "sleep": 0 , "obligatoire":true , "type":"password_changed"},   // Le mot de passe est incorrect
                                            ]
                                        },                           
                        
                                        {"action": "check_if_exist", "xpath":  "//a[(text()='En savoir plus' or text()='Learn more')]/ancestor::div[1][contains(., 'détecté') or contains(., 'detected')]"   , "wait": 3,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist", "xpath": "//a[(text()='En savoir plus' or text()='Learn more')]/ancestor::div[1][contains(., 'détecté') or contains(., 'detected')]", "wait": 1, "sleep": 0 , "obligatoire":true , "type":"Activite_suspecte"},   // Activité suspecte
                                            ]
                                        },
                                        
                                        {"action": "check_if_exist", "xpath": "//input[@id='knowledgePreregisteredEmailInput']", "wait": 2,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist", "xpath": "//input[@id='knowledgePreregisteredEmailInput']", "wait": 1, "sleep": 0 , "obligatoire":true , "type":"code_de_validation"},   // code de validation
                                            ]
                                        }
                                        ,
                                        {"action": "check_if_exist", "xpath": "//input[@type='tel' and @pattern='[0-9 ]*']", "wait": 2,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist", "xpath": "//input[@type='tel' and @pattern='[0-9 ]*']", "wait": 1, "sleep": 0 , "obligatoire":true , "type":"others"},   // others
                                            ]
                                        },
                                        // input[@type="tel" and @pattern="[0-9 ]*"]

                                        {"action": "check_if_exist", "xpath": '//button[span[contains(text(), "Télécharger vos données") or contains(text(), "Download your data")]]', "wait": 2,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist", "xpath": '//button[span[contains(text(), "Télécharger vos données") or contains(text(), "Download your data")]]', "wait": 1, "sleep": 0 ,  "obligatoire":true , "type":"Activite_suspecte"},   //Activité suspecte
                                            ]
                                        }, 

                                        {"action": "check_if_exist",   "xpath": '//input[@type="tel" and @id="phoneNumberId"]', "wait": 30,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist",  "xpath": '//input[@type="tel" and @id="phoneNumberId"]', "wait": 1, "sleep": 0 ,  "obligatoire":true , "type":"code_de_validation"},   //code_de_validation
                                            ]
                                        }, 
                                    ]
                                }  
                                
                            ]
                        },

                        {"action": "check_if_exist", "xpath": "(//div[@data-challengeid])[last()]", "wait": 3, "sleep": 2,  // pour recovry if exist 
                            "sub_action": [
                                {"action": "click", "xpath": "(//div[@data-challengeid])[last()]" ,"wait": 1, "sleep": 5},
                                {"action": "send_keys", "xpath": "//input[@id='knowledge-preregistered-email-response']", "value":"__recovry__","wait": 1,"sleep": 0}, //pour input recovry 
                                {"action": "press_keys", "xpath": "//button[.//span[text()='Suivant']] | //button[.//span[text()='Next']]", "wait": 1, "sleep": 3 ,  
                                    "sub_action": [
                                        {"action": "check_if_exist", "xpath": "//div[@aria-live='polite']//div[@aria-hidden='true']/following-sibling::div//span", "wait": 3,"sleep": 0, 
                                            "sub_action": [
                                                {"action": "check_if_exist", "xpath": "//div[@aria-live='polite']//div[@aria-hidden='true']/following-sibling::div//span", "wait": 2, "sleep": 0  , "obligatoire":true , "type":"recovry_incorrect"},   //Le recovry est incorrect
                                            ]
                                        }                            
                                    ]
                                }
                            ]
                        }
                    ]
                },

                {"action": "check_if_exist", "xpath":"//div[@id='main-message']", "wait": 1, "sleep": 0,
                    "sub_action": [
                        {"action": "click", "xpath": "//div[@id='main-message']", "sleep": 0, "wait": 5 , "obligatoire":true , "type":"bad_proxy"}
                    ]
                }, 

                //   arrete ici pas triter pourqui 
                {"action": "check_if_exist", "xpath": "//div[@data-secondary-action-label='Not now']|//div[@data-secondary-action-label='Pas maintenant']", "wait": 3,"sleep": 0, //div Not now 
                    "sub_action": [
                        {"action": "click", "xpath": "//div[@data-secondary-action-label='Not now']/div/div[2]/div/div/button|//div[@data-secondary-action-label='Pas maintenant']/div/div[2]/div/div/button", "wait": 2, "sleep": 0},   //button  Not now 
                    ]
                },

                {"action": "check_if_exist", "xpath": "//button[@aria-label='Save' or @aria-label='Sauvegarder']", "wait": 3,"sleep": 0, 
                    "sub_action": [
                        {"action": "click", "xpath": "//button[@aria-label='Save' or @aria-label='Sauvegarder']", "wait": 1, "sleep": 3},   //button Save 
                    ]
                },

                {"action": "check_if_exist", "xpath": "//button[@aria-label='Skip' or @aria-label='Sauter']", "wait": 3,"sleep":0 , //div Not now 
                    "sub_action": [
                        {"action": "click", "xpath": "//button[@aria-label='Skip' or @aria-label='Sauter']", "wait": 1, "sleep": 3},   //button  Not now 
                    ]
                }
              
            ]
        }
    ],
    "report_spam": [
        {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']/div/div[2]/div[2]", "wait": 3, "sleep": 3},
        {"action": "check_if_exist", "xpath": "//button[span[text()='Report spam'] or span[text()='Spam']]", "wait": 2,"sleep": 0, 
            "sub_action": [
                {"action": "click", "xpath": "//button[span[text()='Report spam'] or span[text()='Spam']]", "wait": 2, "sleep": 0},  
            ]
        }
    ],
    "delete": [
        {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']/div/div[2]/div[3] | //div[@gh='mtb']/div/div/div[2]/div[3]", "wait": 3, "sleep": 3}
    ],
    "not_spam": [
        {"action": "dispatchEvent", "xpath": "(//div[@gh='mtb']/div/div[count(div)=2][1]/div[1][count(div)=1] | //div[@gh='mtb']/div/div[count(div)=1][3]/div[1] | //div[@gh='mtb']/div[count(div)=1]/div/div[count(div)=1][3]/div[1] | //div[@gh='mtb']/div[count(div)=1]/div/div[count(div)=2]/div[1])[1]", "wait": 3, "sleep": 3}
    ],
    "click_link": [
        {"action": "search_for_link_and_click", "xpath": "(//div[@data-message-id])[1]/div[2]/div[3]/div[3]/div[1]//a[@href]", "wait": 10, "sleep": 3},    ],
    "open_inbox": [
        {"action": "open_url", "url": "https://mail.google.com/mail/u/0/#inbox", "wait": 1, "sleep": 5  ,     
            "sub_action": [
                            {"action": "check_if_exist", "xpath": "(//button[@aria-label='Cancel' or @aria-label='Annuler']) | (//button[@aria-label='Sauter' or @aria-label='Skip']) | (//figure[contains(@aria-hidden, 'true')]//img)[1]", "wait": 3,"sleep": 0, 

                                "sub_action": [
                                    {"action": "check_if_exist", "xpath": "//button[@aria-label='Cancel' or @aria-label='Annuler']", "wait": 3,"sleep": 0, 
                                        "sub_action": [
                                            {"action": "click", "xpath": "//button[@aria-label='Cancel' or @aria-label='Annuler']", "wait": 2, "sleep": 0 },   
                                        ]
                                    },                           
                    
                                    {"action": "check_if_exist", "xpath":  "//button[@aria-label='Sauter' or @aria-label='Skip']"   , "wait": 3,"sleep": 0, 
                                        "sub_action": [
                                            {"action": "click", "xpath": "//button[@aria-label='Sauter' or @aria-label='Skip']", "wait": 1, "sleep": 0 },  
                                        ]
                                    },
                                    
                                    {"action": "check_if_exist", "xpath": "(//figure[contains(@aria-hidden, 'true')]//img)[1]", "wait": 3,"sleep": 0, 
                                        "sub_action": [
                                            {"action": "open_url", "url": "https://mail.google.com/mail/u/0/#inbox", "wait": 1, "sleep": 0 }, 
                                        ]
                                    }
                                    
                            
                                ]
                            }  
                            
                        ]
        
        },
    ],
    "open_spam": [
        {"action": "open_url", "url": "https://mail.google.com/mail/u/0/#spam", "wait": 1, "sleep": 5},

    ],
    "archive": [
      {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[2]/div[1]", "wait": 5, "sleep": 1}
    ],
    "next": [
        {"action": "check_if_exist", "xpath": "//div[@class='nH bkK']/div/div/div/div[@class='aeH']/div[@gh]/div[2]/div[1]/div/div[2][@role='button' and not(@aria-disabled='true')]", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "click", "xpath": "//div[@class='nH bkK']/div/div/div/div[@class='aeH']/div[@gh]/div[2]/div[1]/div/div[2][@role='button' and not(@aria-disabled='true')]", "wait": 1, "sleep": 0}
         ]}
    ],
    "next_page": [
        {"action": "check_if_exist", "xpath": "//div[@gh]/div[@class='nH aqK']/div[@class='Cr aqJ']/div[1]/span/div[3][@role='button' and not(@aria-disabled)]", "wait": 1, "sleep": 0,
             "sub_action": [
                 {"action": "dispatchEvent", "xpath": "//div[@gh]/div[@class='nH aqK']/div[@class='Cr aqJ']/div[1]/span/div[3][@role='button' and not(@aria-disabled)]", "wait": 1, "sleep": 0}
             ]}
    ],
    "CHECK_NEXT": [   //next page
        {"action": "check", "xpath": "//div[@gh]/div[@class='nH aqK']/div[@class='Cr aqJ']/div[1]/span/div[3][@role='button' and not(@aria-disabled)] | //div[@class='nH bkK']/div/div/div/div[@class='aeH']/div[@gh]/div[2]/div[1]/div/div[2][@role='button' and not(@aria-disabled='true')]", "wait": 1, "sleep": 0}
    ],
    "CHECK_FOLDER": [  //check sur message 
        {"action": "check", "xpath": "(//div[@role='main' and @class]//div[@jsaction]//table/tbody/tr[1]/td[@role='gridcell'])[1]", "wait": 5, "sleep": 1}
    ],
    "is_empty_folder": [
        {"action": "check", "xpath": "(//div[@role='main' and @class]//div[@jsaction]//table/tbody/tr[1]/td[@role='gridcell'])[1]", "wait": 5, "sleep": 1}
    ],
    "is_last_message": [  //last message 
        {"action": "check", "xpath": "//div[@class='nH bkK']/div/div/div/div[@class='aeH']/div[@gh]/div[2]/div[1]/div/div[2][@role='button' and (@aria-disabled='true')]", "wait": 5, "sleep": 1}
    ],
    "open_message": [
        {"action": "click", "xpath": "(//div[@role='main' and @class]//div[@jsaction]//table/tbody/tr[1]/td[@role='gridcell'])[1]", "wait": 10, "sleep": 1}
    ],
    "OPEN_MESSAGE_ONE_BY_ONE": [
        {"action": "click", "xpath": "(//div[@role='main' and @class]//div[@jsaction]//table/tbody/tr[1]/td[@role='gridcell'])[1]", "wait": 10, "sleep": 1}
    ],

    "search": [
        {"action": "send_keys", "xpath": "//input[@name='q']", "value": "__search__", "wait": 5, "sleep": 1},
        {"action": "press_keys", "xpath": '//button[@aria-label="Rechercher dans les messages" and @role="button"] | //button[@aria-label="Search mail" and @role="button"]', "wait": 1, "sleep": 7}
    ],
    "select_all": [
        {"action": "dispatchEvent", "xpath": "//div[@class='Cq aqL' and @gh='mtb']/div/div/div/div/div/div[@aria-hidden='true']", "wait": 10, "sleep": 1 },
        {"action": "dispatchEventTwo", "xpath": "//div/div[@gh='tm']//div[@selector='all' and @role='menuitem']", "wait": 3, "sleep": 1}
    ],
    "mark_as_important": [
        {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button']", "wait": 5, "sleep": 0},
        {"action": "check_if_exist", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[28][@role='menuitem']", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEventTwo", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[28][@role='menuitem']", "wait": 1, "sleep": 1},
             {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button']", "wait": 5, "sleep": 1},
         ]},
        {"action": "check_if_exist", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[4][not(@aria-disabled='true')]", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEventTwo", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX' ]/div[4][not(@aria-disabled='true')]", "wait": 2, "sleep": 0}
         ]},
        {"action": "check_if_exist", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button' and @aria-expanded='true']", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button' and @aria-expanded='true']", "wait": 1, "sleep": 0}
         ]}
    ],
    "add_star": [
        {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button']", "wait": 5, "sleep": 1},
        {"action": "check_if_exist", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[28][@role='menuitem']", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEventTwo", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[28][@role='menuitem']", "wait": 1, "sleep": 1},
             {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button']", "wait": 5, "sleep": 1},
         ]},
        {"action": "check_if_exist", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[7][not(@aria-disabled='true')]", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEventTwo", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[7][not(@aria-disabled='true')]", "wait": 2, "sleep": 0}
         ]},
        {"action": "check_if_exist", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button' and @aria-expanded='true']", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button' and @aria-expanded='true']", "wait": 1, "sleep": 0}
         ]}
    ],
    "mark_as_read": [
        {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button']", "wait": 5, "sleep": 1},
        {"action": "check_if_exist", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[28][@role='menuitem']", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEventTwo", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX']/div[28][@role='menuitem']", "wait": 1, "sleep": 1},
             {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button']", "wait": 5, "sleep": 1},
         ]},
        {"action": "check_if_exist", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX' ]/div[3][not(@aria-disabled='true')]", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEventTwo", "xpath": "//div[@role='menu' and @aria-haspopup='true' and not(contains(@style,'display: none;'))]/div[@class='SK AX' ]/div[3][not(@aria-disabled='true')]", "wait": 2, "sleep": 0}
         ]},
        {"action": "check_if_exist", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button' and @aria-expanded='true']", "wait": 1, "sleep": 0,
         "sub_action": [
             {"action": "dispatchEvent", "xpath": "//div[@gh='mtb']//div[@class='G-tF']/div[@class='G-Ni J-J5-Ji'][last()]/div[@role='button' and @aria-expanded='true']", "wait": 1, "sleep": 0}
         ]}
    ],
    "reply_message": [
        {"action": "click", "xpath": "(//div[@data-message-id])[1]/div[2]/div[1]/table/tbody/tr/td[4]/div[@role='button'][2]", "wait": 5, "sleep": 1 },
        {"action": "send_keys_Reply", "xpath": "//div[@role='textbox']", "value": "__reply_message__", "wait": 3, "sleep": 1},
        {"action": "click", "xpath": "//table[@role='group']/tbody/tr/td[1]/div[1]/div[2]/div[@role='button'][1]", "wait": 10, "sleep": 5}
    ],
    "change_password": [
        {"action": "open_url", "url": "https://myaccount.google.com/security", "sleep": 5},
        {"action": "click", "xpath": "//a[contains(@href,'signinoptions/rescuephone')]", "wait": 5, "sleep": 1 },
        {"action": "check_if_exist", "xpath": "//input[@type='password']", "wait": 5, "sleep": 0,
            "sub_action": [
                {"action": "send_keys", "xpath": "//input[@type='password']", "value": "__password__", "wait": 5, "sleep": 1},
                {"action": "press_keys", "xpath": "//button[.//span[text()='Suivant']] | //button[.//span[text()='Next']]", "wait": 1, "sleep": 5}
            ]
        },
        {"action": "check_if_exist", "xpath": "(//div[@data-challengeid])[last()]", "wait": 5, "sleep": 0, "sub_action": [
            {"action": "click", "xpath": "(//div[@data-challengeid])[last()]", "wait": 5, "sleep": 1},
            {"action": "send_keys", "xpath": "//input[@id='knowledge-preregistered-email-response']", "value": "__recovry__" , "wait": 5, "sleep": 1},
            {"action": "press_keys", "xpath": "//button[.//span[text()='Suivant']] | //button[.//span[text()='Next']]", "wait": 1, "sleep": 5},
        ]},
        {"action": "replace_url_1", "wait": 1, "sleep": 3},
        {"action": "send_keys", "xpath": "(//input[@type='password'])[1]", "value": "__newPassword__", "wait": 5, "sleep": 1},
        {"action": "send_keys", "xpath": "(//input[@type='password'])[2]", "value": "__newPassword__", "wait": 5, "sleep": 1},
        {"action": "click", "xpath": "//button[@type='submit']", "wait": 5, "sleep": 3},
        {"action": "click", "xpath": "//a[contains(@href,'signinoptions/rescuephone')]", "wait": 5, "sleep": 1}
    ],
    "change_recovery": [
        {"action": "open_url", "url": "https://myaccount.google.com/security", "sleep": 5},
        {"action": "click", "xpath": "//a[contains(@href,'signinoptions/rescuephone')]", "wait": 5, "sleep": 1},
        {"action": "check_if_exist", "xpath": "//input[@type='password']", "wait": 5, "sleep": 0, "sub_action": [
            {"action": "send_keys", "xpath": "//input[@type='password']", "value": "password", "wait": 5, "sleep": 1},
            {"action": "press_keys", "xpath": "//button[.//span[text()='Suivant']] | //button[.//span[text()='Next']]",  "wait": 1, "sleep": 5},
        ]},
        {"action": "check_if_exist", "xpath": "(//div[@data-challengeid])[last()]", "wait": 5, "sleep": 0,"sub_action": [
             {"action": "click", "xpath": "(//div[@data-challengeid])[last()]", "wait": 5, "sleep": 1},
             {"action": "send_keys", "xpath": "//input[@id='knowledge-preregistered-email-response']","value": "__recovry__" , "wait": 5, "sleep": 1},
             {"action": "press_keys", "xpath": "//button[.//span[text()='Suivant']] | //button[.//span[text()='Next']]", "wait": 1, "sleep": 5}
         ]},
        {"action": "replace_url_2", "wait": 1, "sleep": 3},
        {"action": "clear", "xpath": "//input[@type='email']", "wait": 5, "sleep": 1},
        {"action": "send_keys", "xpath": "//input[@type='email']", "value": "__newRecovry__" , "wait": 5, "sleep": 1},
        {"action": "click", "xpath": "//button[@type='submit']", "wait": 5, "sleep": 3}
    ],
    "add_contacts": [
    //    {"action": "contact", "wait": 1, "sleep": 3}
        {"action": "check_if_exist", "xpath":"//input[@aria-label='Email' or @aria-label='E-mail']", "wait": 5, "sleep": 2, "sub_action": [
            {"action": "send_keysHumain", "xpath": "//input[@aria-label='Email' or @aria-label='E-mail']", "value": "__Email_Contact__" , "wait": 5, "sleep": 1},
            {"action": "dispatchEventTwo", "xpath": "//button[@aria-label='Enregistrer'] | //button[@aria-label='Save']", "wait": 2, "sleep": 0},
            {"action": "check_if_exist", "xpath":"//button[contains(., 'Fusionner') or contains(., 'Merge')]", "wait": 5, "sleep": 2, "sub_action": [
                {"action": "press_keys", "xpath": "//button[contains(., 'Fusionner') or contains(., 'Merge')]", "value": "__Email_Contact__" , "wait": 5, "sleep": 1},
            ]},
        ]},
   
    ]
    ,
    "return_back":[
        {"action": "dispatchEvent", "xpath": "//div[@role='button' and (starts-with(@title, 'Retour') or starts-with(@title,'Back') or starts-with(@aria-label, 'Back to') or starts-with(@aria-label, 'Retour'))]", "wait": 5, "sleep": 1 }

    ],
    "google_preferred_addresses": [
        {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 5, "sleep": 0, "sub_action": [
            {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "value":"__search_value__" ,"wait": 5, "sleep": 1},
            {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 5},
            {"action": "check_if_exist", "xpath": "//div[@role='region'][.//div//button[(@aria-label='Partager' or @aria-label='Share') ]]", "wait": 5, "sleep": 0, "sub_action": [
                {"action": "click", "xpath": "//button[@aria-label='Save' or @aria-label='Sauvegarder' or @aria-label='Enregistrer' ]",  "wait": 1, "sleep": 5 },
                {"action": "check_if_exist", "xpath": "//div[@id='action-menu']", "wait": 5, "sleep": 0, "sub_action": [
                    {"action": "check_if_exist", "xpath": "//div[@role='menuitemradio' and @aria-checked='false' and (.//*[normalize-space(text())='Starred places' or normalize-space(text())='Lieux étoilés' or normalize-space(text())='Lieux favoris'  or normalize-space(text())='Favorite places'   ])]", "wait": 5, "sleep": 0, "sub_action": [
                        {"action": "click", "xpath": "//div[@role='menuitemradio' and @aria-checked='false' and (.//*[normalize-space(text())='Starred places' or normalize-space(text())='Lieux étoilés' or normalize-space(text())='Lieux favoris'  or normalize-space(text())='Favorite places'   ])]",  "wait": 1, "sleep": 2},
                    ]},
                ]}
                
            ]},
        ]}
   
    ],
    "google_places_to_visit": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 5, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']","search":"__search_value__" , "wait": 5, "sleep": 1},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 5},
        {"action": "check_if_exist", "xpath": "//div[@role='region'][.//div//button[(@aria-label='Partager' or @aria-label='Share') ]]", "wait": 5, "sleep": 0, "sub_action": [
            {"action": "click", "xpath": "//button[@aria-label='Save' or @aria-label='Sauvegarder' or @aria-label='Enregistrer' ]",  "wait": 1, "sleep": 5 },
            {"action": "check_if_exist", "xpath": "//div[@id='action-menu']", "wait": 5, "sleep": 0, "sub_action": [
                        {"action": "check_if_exist", "xpath": "//div[@role='menuitemradio' and @aria-checked='false' and (.//*[normalize-space(text())='Want to go' or normalize-space(text())='Je veux y aller' or  normalize-space(text())='À visiter' or  normalize-space(text())='To be visited'     ])]", "wait": 5, "sleep": 0, "sub_action": [
                            {"action": "click", "xpath": "//div[@role='menuitemradio' and @aria-checked='false' and (.//*[normalize-space(text())='Want to go' or normalize-space(text())='Je veux y aller' or  normalize-space(text())='À visiter' or  normalize-space(text())='To be visited'     ])]",  "wait": 1, "sleep": 2},
                        ]},
                    ]}
            // ]},
        ]}
    ],
    "google_travel_projects": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 5, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "search":"__search_value__" , "wait": 5, "sleep": 1},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 5},
        {"action": "check_if_exist", "xpath": "//div[@role='region'][.//div//button[(@aria-label='Partager' or @aria-label='Share') ]]", "wait": 5, "sleep": 0, "sub_action": [
                {"action": "click", "xpath": "//button[@aria-label='Save' or @aria-label='Sauvegarder' or @aria-label='Enregistrer' ]",  "wait": 1, "sleep": 5  },
                {"action": "check_if_exist", "xpath": "//div[@id='action-menu']", "wait": 5, "sleep": 0, "sub_action": [
                    {"action": "check_if_exist", "xpath": "//div[@role='menuitemradio' and @aria-checked='false' and (.//*[normalize-space(text())='Travel plans' or normalize-space(text())='Projets de voyage'  or  normalize-space(text())='Projets de voyages'  or    normalize-space(text())='Travel projects'   ])]", "wait": 5, "sleep": 0, "sub_action": [
                        {"action": "click", "xpath": "//div[@role='menuitemradio' and @aria-checked='false' and (.//*[normalize-space(text())='Travel plans' or normalize-space(text())='Projets de voyage'  or  normalize-space(text())='Projets de voyages'  or    normalize-space(text())='Travel projects'   ])]",  "wait": 1, "sleep": 2},
                    ]},
                ]}
            ]},
        // ]}
    ],
    "google_favorite_places": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 5, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "search":"__search_value__" , "wait": 5, "sleep": 1},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 5},
        {"action": "check_if_exist", "xpath": "//div[@role='region'][.//div//button[(@aria-label='Partager' or @aria-label='Share') ]]", "wait": 5, "sleep": 0, "sub_action": [
                {"action": "click", "xpath": "//button[@aria-label='Save' or @aria-label='Sauvegarder' or @aria-label='Enregistrer' ]",  "wait": 1, "sleep": 5 },
                {"action": "check_if_exist", "xpath": "//div[@id='action-menu']", "wait": 5, "sleep": 0, "sub_action": [
                    {"action": "check_if_exist", "xpath": "//div[@role='menuitemradio'  and @aria-checked='false'  and (.//*[normalize-space(text())='Favorites' or normalize-space(text())='Favoris' or normalize-space(text())='Favorite places' or normalize-space(text())='Lieux favoris'   ])]", "wait": 5, "sleep": 0, "sub_action": [
                        {"action": "click", "xpath": "//div[@role='menuitemradio'  and @aria-checked='false'  and (.//*[normalize-space(text())='Favorites' or normalize-space(text())='Favoris' or normalize-space(text())='Favorite places' or normalize-space(text())='Lieux favoris'   ])]",  "wait": 1, "sleep": 2},
                    ]},
                ]}
            // ]},
        ]}
   
    ],



    "google_hotels": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 3, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "value": "Tanger", "wait": 2, "sleep": 0},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 1},
        {"action": "check_if_exist", "xpath": "((//div[@role='region' and (@aria-roledescription='carousel' or @aria-roledescription='carrousel') ])[1])/div[2]/div[2]", "wait": 5, "sleep": 0, "sub_action": [
                    {"action": "check_if_exist", "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Hotels' or normalize-space(.)='Hôtels')]]", "wait": 5, "sleep": 0, "sub_action": [
                            {"action": "click", "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Hotels' or normalize-space(.)='Hôtels')]]",  "wait": 1, "sleep": 3},
                    ]}
            // ]},
        ]}
   
    ],
    "google_restaurants": [
            // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 3, "sleep": 0, "sub_action": [
            // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "wait": 2, "sleep": 0},
            // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 1},
            {"action": "check_if_exist", "xpath": "((//div[@role='region' and (@aria-roledescription='carousel' or @aria-roledescription='carrousel') ])[1])/div[2]/div[2]", "wait": 5, "sleep": 0, "sub_action": [
                        {"action": "check_if_exist", "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Restaurants' or normalize-space(.)='Restaurants')]]", "wait": 5, "sleep": 0, "sub_action": [
                                {"action": "click", "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Restaurants' or normalize-space(.)='Restaurants')]]",  "wait": 1, "sleep": 3},
                        ]}
                // ]},
            ]},

    
        ],
    "google_attractions": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 3, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "value": "Tanger", "wait": 2, "sleep": 0},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 1},
        {"action": "check_if_exist", "xpath": "((//div[@role='region' and (@aria-roledescription='carousel' or @aria-roledescription='carrousel') ])[1])/div[2]/div[2]", "wait": 5, "sleep": 0, "sub_action": [
                    {
                        "action": "check_if_exist",
                        "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Choses à faire' or normalize-space(.)='Things to do' or normalize-space(.)='Activités à découvrir' or normalize-space(.)='Activities to discover')]]",
                        "wait": 5,
                        "sleep": 0,
                        "sub_action": [
                            {
                            "action": "click",
                            "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Choses à faire' or normalize-space(.)='Things to do' or normalize-space(.)='Activités à découvrir' or normalize-space(.)='Activities to discover')]]",
                            "wait": 1,
                            "sleep": 3
                            }
                        ]
                    }

            // ]},
        ]}

    ],
    "google_museums": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 3, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "value": "Tanger", "wait": 2, "sleep": 0},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 1},
        {"action": "check_if_exist", "xpath": "((//div[@role='region' and (@aria-roledescription='carousel' or @aria-roledescription='carrousel') ])[1])/div[2]/div[2]", "wait": 5, "sleep": 0, "sub_action": [
                {
                    "action": "check_if_exist",
                    "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Musées' or normalize-space(.)='Museums')]]",
                    "wait": 5,
                    "sleep": 0,
                    "sub_action": [
                        {
                        "action": "click",
                        "xpath":  "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Musées' or normalize-space(.)='Museums')]]",
                        "wait": 1,
                        "sleep": 3
                        }
                    ]
                }

            // ]},
        ]}

    ],
    "google_transit": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 3, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "value": "Tanger", "wait": 2, "sleep": 0},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 1},
        {"action": "check_if_exist", "xpath": "((//div[@role='region' and (@aria-roledescription='carousel' or @aria-roledescription='carrousel') ])[1])/div[2]/div[2]", "wait": 5, "sleep": 0, "sub_action": [
                {
                    "action": "check_if_exist",
                    "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Transports en commun' or normalize-space(.)='Public transport' or normalize-space(.)='Transit')]]",
                    "wait": 5,
                    "sleep": 0,
                    "sub_action": [
                        {
                        "action": "click",
                        "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Transports en commun' or normalize-space(.)='Public transport' or normalize-space(.)='Transit')]]",
                        "wait": 1,
                        "sleep": 3
                        }
                    ]
                }

            // ]},
        ]}

    ],    
    "google_pharmacies": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 3, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "value": "Tanger", "wait": 2, "sleep": 0},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 1},
        {"action": "check_if_exist", "xpath": "((//div[@role='region' and (@aria-roledescription='carousel' or @aria-roledescription='carrousel') ])[1])/div[2]/div[2]", "wait": 5, "sleep": 0, "sub_action": [
                {
                    "action": "check_if_exist",
                    "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Pharmacies' or normalize-space(.)='Pharmacies')]]",
                    "wait": 5,
                    "sleep": 0,
                    "sub_action": [
                        {
                        "action": "click",
                        "xpath":  "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='Pharmacies' or normalize-space(.)='Pharmacies')]]",
                        "wait": 1,
                        "sleep": 3
                        }
                    ]
                }

            // ]},
        ]}

    ],
    "google_atms": [
        // {"action": "check_if_exist", "xpath": "//input[@id='searchboxinput']", "wait": 3, "sleep": 0, "sub_action": [
        // {"action": "send_keys", "xpath": "//input[@id='searchboxinput']", "value": "Tanger", "wait": 2, "sleep": 0},
        // {"action": "press_keys", "xpath": "//button[@id='searchbox-searchbutton']",  "wait": 1, "sleep": 1},
        {"action": "check_if_exist", "xpath": "((//div[@role='region' and (@aria-roledescription='carousel' or @aria-roledescription='carrousel') ])[1])/div[2]/div[2]", "wait": 5, "sleep": 0, "sub_action": [
                {
                    "action": "check_if_exist",
                    "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='distributeurs automatiques de billets' or normalize-space(.)='Distributeurs de billets' or normalize-space(.)='ATMs')]]",
                    "wait": 5,
                    "sleep": 0,
                    "sub_action": [
                        {
                        "action": "click",
                        "xpath": "//button[.//span[contains(@class, 'fontTitleSmall') and (normalize-space(.)='distributeurs automatiques de billets' or normalize-space(.)='Distributeurs de billets' or normalize-space(.)='ATMs')]]",
                        "wait": 1,
                        "sleep": 3
                        }
                    ]
                }

            // ]},
        ]}

    ],
    "google_trends": [
        {"action": "scrollTo",  "value": 1000,  "sleep": 1},

        {
            "action": "scroll_to_xpath",
            "xpath": "//button[.//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'sign up' or normalize-space(text())=concat('S', \"'\", 'inscrire')]]",
            "wait": 1,
            "sleep": 5
        },
        {
            "action": "check_if_exist",
            "xpath": "//button[.//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'sign up' or normalize-space(text())=concat('S', \"'\", 'inscrire')]]",
            "wait": 5,
            "sleep": 0,
            "sub_action": [
                {
                    "action": "click",
                    "xpath": "//button[.//*[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'sign up' or normalize-space(text())=concat('S', \"'\", 'inscrire')]]",
                    "wait": 1,
                    "sleep": 5
                }
            ]
        }
    ],


    "news_google": [

        {
            "action": "scroll_to_xpath","xpath": "//main/div[2]/c-wiz/section/div[2]/div", "wait": 1,"sleep": 2
        },
        {
            "action": "check_if_exist","xpath": "//main/div[2]/c-wiz/section/div[2]/div", "wait": 3,"sleep": 1,  "sub_action": [
                {
                    "action": "click_random_link","container_xpath": "//main/div[2]/c-wiz/section/div[2]/div", "child_selector": "a[href]",  "wait": 2,"sleep": 3
                },
            ]
        }
    ],
    "youtube_Shorts": [
        {"action": "Loop",  "limit_loop": "__Loop__Count__" ,  "sleep": 3  , "sub_action": [
            {"action": "check_if_exist", "xpath": "//*[@id='actions']/*[@id='like-button']", "wait": 5, "sleep": 3, "sub_action": [
                {"action": "check_if_exist", "xpath": "//*[@id='like-button']//button[@aria-pressed='false']", "wait": 5, "sleep": 3, "sub_action": [
                    {"action": "click", "xpath": "//*[@id='like-button']//button[@aria-pressed='false']",  "wait": 2, "sleep": 3},
                ]},
                {"action": "check_if_exist", "xpath": "//button[contains(@aria-label, 'commentaires') or contains(@aria-label, 'comments')]", "wait": 4, "sleep": 2 , "sub_action": [
                    {"action": "click",  "xpath": "//button[contains(@aria-label, 'commentaires') or contains(@aria-label, 'comments')]", "wait": 2, "sleep": 3 },
                    {"action": "check_if_exist", "xpath": "//*[@id='placeholder-area']",  "wait": 5, "sleep": 3  ,"sub_action": [
                        {"action": "click", "xpath": "//*[@id='placeholder-area']",  "wait": 1, "sleep": 3 },
                        {"action": "check_if_exist", "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']",  "wait": 5, "sleep": 4,  "sub_action": [
                            {"action": "focus", "xpath":  "//div[@id='contenteditable-root' and @contenteditable='true']", "wait": 3, "sleep": 1},
                            {"action": "click", "xpath":  "//div[@id='contenteditable-root' and @contenteditable='true']",  "wait": 3, "sleep": 3},
                            {"action": "insertText", "xpath":  "//div[@id='contenteditable-root' and @contenteditable='true']", "value" : "randomComments" , "wait": 1, "sleep": 5},
                            {"action": "check_if_exist", "xpath": "//ytd-button-renderer[@id='submit-button']//button", "wait": 5, "sleep": 4, "sub_action": [
                                {"action": "click", "xpath": "//ytd-button-renderer[@id='submit-button']//button",  "wait": 1, "sleep": 7},
                            ]},
                            {"action": "check_if_exist", "xpath": "(//*[@id='visibility-button']//button[@aria-label='Close' or @aria-label='Fermer'])[1]", "wait": 5, "sleep": 4, "sub_action": [
                                {"action": "click", "xpath": "(//*[@id='visibility-button']//button[@aria-label='Close' or @aria-label='Fermer'])[1]" ,  "wait": 3, "sleep": 4},
                            ]},
                        ]},
                    ]},
                ]},
            
            
             
                {"action": "check_if_exist", "xpath": "//button[@aria-disabled='false' and (@aria-label='Vidéo suivante' or @aria-label='Next video')]", "wait": 4, "sleep": 4, "sub_action": [
                    {"action": "click", "xpath": "//button[@aria-disabled='false' and (@aria-label='Vidéo suivante' or @aria-label='Next video')]",  "wait": 1, "sleep": 3},
                ]},
            ]}
        ]},
    ],
    "youtube_charts": [
        {"action": "Sub_Open_Tab", "wait": 2, "sleep": 1 ,  "limit_loop": "__Loop__Count__" }
    ],
    "CheckLoginYoutube": [
        {"action": "check_if_exist", "xpath": "(//a[starts-with(@href, 'https://accounts.google.com/ServiceLogin')])[1]", "wait": 5, "sleep": 2,  
            "sub_action": [
                {
                    "action": "click", "xpath": "(//a[starts-with(@href, 'https://accounts.google.com/ServiceLogin')])[1]", "wait": 5, "sleep": 0,  
                },
                {
                    "action": "check_if_exist",  "xpath": "//div[@role='link' and @data-identifier and .//div[@data-email]]", "wait": 3, "sleep": 0,
                        "sub_action": [
                            {"action": "click",  "xpath": "//div[@role='link' and @data-identifier and .//div[@data-email]]", "wait": 3, "sleep": 0},
                        ]
                },
                {
                    "action": "check_if_exist",  "xpath": "//input[@type='password']", "wait": 3, "sleep": 0,
                        "sub_action": [
                            {"action": "send_keys",  "xpath": "//input[@type='password']" , "value":"__password__", "wait": 3, "sleep": 0},
                            {"action": "press_keys",  "xpath":"//button[.//span[text()='Suivant']] | //button[.//span[text()='Next']]"  , "wait": 3, "sleep": 0}
                        ]
                }

            ]
        }
    ],

    // "youtube_trending": [
    //     {"action": "scrollTo",  "value": 1000,  "sleep": 1},
    //     {"action": "check_if_exist", "xpath": "(//button-view-model[@class='yt-spec-button-view-model']//button[(contains(@title, 'like this content') or contains(@title, \"J'aime ce contenu\"))and .//yt-icon])[1]", "wait": 3, "sleep": 0, "sub_action": [
    //         {"action": "click",  "xpath": "(//button-view-model[@class='yt-spec-button-view-model']//button[(contains(@title, 'like this content') or contains(@title, \"J'aime ce contenu\"))and .//yt-icon])[1]", "wait": 1, "sleep": 3}
    //     ]},
    //     {"action": "check_if_exist", "xpath": "//*[@id='placeholder-area']", "wait": 3, "sleep": 0, "sub_action": [
    //         {"action": "click",  "xpath": "//*[@id='placeholder-area']", "wait": 1, "sleep": 3}
    //     ]},
    //     {"action": "check_if_exist", "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']" , "wait": 3, "sleep": 0, "sub_action": [
    //         {"action": "focus",  "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']", "wait": 1, "sleep": 3},
    //         {"action": "click",  "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']", "wait": 1, "sleep": 3},
    //         {"action": "insertText", "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']", "value" : "randomComments" , "wait": 1, "sleep": 5}

    //     ]},
    //     {"action": "check_if_exist", "xpath": "//button[@aria-disabled='false' and (@aria-label='Ajouter un commentaire' or @aria-label='Add a comment')]", "wait": 3, "sleep": 0, "sub_action": [
    //         {"action": "click",  "xpath": "//button[@aria-disabled='false' and (@aria-label='Ajouter un commentaire' or @aria-label='Add a comment')]" , "wait": 1, "sleep": 3}
    //     ]},
    // ]
}



