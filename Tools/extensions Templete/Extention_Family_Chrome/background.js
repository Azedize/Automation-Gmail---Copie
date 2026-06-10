

chrome.runtime.onInstalled.addListener(() => {
    configureProxyDirectly(__host__, __port__, __user__, __pass__);
});



chrome.runtime.onStartup.addListener(() => {
    configureProxyDirectly(__host__, __port__, __user__, __pass__);
});





function saveLog(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    const emojis = ["🔔"];
    const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)];
    chrome.storage.local.get({ logs: [] }, (data) => {
        const updatedLogs = [...(data.logs || []), `${randomEmoji} ${logMessage}`];
        chrome.storage.local.set({ logs: updatedLogs });
    });
}





chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (
        changeInfo.status === "complete" &&
        tab.url === "https://www.youtube.com/"
    ) {
        // saveLog("👺👺👺👺👺 [background] Changement détecté dans un onglet YouTube :", tabId);

        // 🔐 Lecture du local storage
        const { sentMessages } = await chrome.storage.local.get("sentMessages");

        if (sentMessages && sentMessages.length > 0) {
            // saveLog("📦👺 [background] Données 'sentMessages' trouvées :", sentMessages);
            await sleep(5000)

            // Ici vous pouvez faire des vérifications supplémentaires comme :
            const isMonitoredTab = sentMessages.some(item => item.TabId === tabId);

            if (isMonitoredTab) {
                // saveLog("✅👺 [background] L'onglet correspond à un ID enregistré. Exécution des actions...");

                // Exemple : fermeture de l'onglet, suppression du stockage, etc.
                try {
                    await chrome.tabs.remove(tabId);
                    // saveLog("🛑👺 Onglet fermé :", tabId);

                    await chrome.storage.local.remove("sentMessages");
                    // saveLog("🧼👺 Clé 'sentMessages' supprimée.");

                    if (callerTabId_CheckLoginYoutube) {
                        await chrome.tabs.sendMessage(callerTabId_CheckLoginYoutube, {
                            action: "Closed_tab_Finished_CheckLoginYoutube"
                        });
                        // saveLog("📨👺 Message envoyé à l'onglet d'origine.");
                    }

                    // Réinitialisation
                    currentMapTabId_CheckLoginYoutube = null;
                    callerTabId_CheckLoginYoutube = null;
                    originalTabIds_CheckLoginYoutube = [];

                    // saveLog("♻️👺 Variables réinitialisées.");

                } catch (err) {
                    saveLog("❌👺 Erreur lors de la fermeture ou du nettoyage :", err);
                }
            } else {
                saveLog("⚠️👺 [background] L'onglet ne correspond pas à ceux surveillés.");
            }
        } else {
            saveLog("📭👺 [background] Aucun 'sentMessages' trouvé dans le stockage local.");
        }
    }
});





chrome.runtime.onInstalled.addListener(() => {
    chrome.alarms.create("reloadAndOpenTabOnce", {
        when: Date.now() ,
    });
});









chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "reloadAndOpenTabOnce") {
        
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length > 0) {
                setTimeout(() => {
                    chrome.tabs.create({ url: "https://accounts.google.com/" });
                }, 500);
            }
        });

        chrome.alarms.clear(alarm.name);
    }
});







let oldTab = null;

function createNewTab(url, onComplete) {
    
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs.length > 0) {
            oldTab = tabs[0];
        }
    });

    chrome.tabs.create({ url }, (tab) => {

        chrome.tabs.onUpdated.addListener(function listener(tabId, changeInfo) {
            if (tabId === tab.id && changeInfo.status === "complete") {
                chrome.tabs.onUpdated.removeListener(listener);
                onComplete(tab); 
            }
        });
    });
}





const processingTabs = {};

chrome.runtime.onInstalled.addListener(() => {
    chrome.tabs.query({ url: "*://mail.google.com/*" }, (tabs) => {
        tabs.forEach((tab) => {
            chrome.tabs.reload(tab.id);
        });
    });
});




chrome.webNavigation.onCompleted.addListener((details) => {
    console.log("➡️​➡️​➡️​➡️​➡️​➡️​➡️​➡️​Navigation completed:", details);

    const ignoredUrls = [
        "https://contacts.google.com",
        "https://www.google.com/maps",
        "https://trends.google.com/trends/"
    ];

    const monitoredPatterns = [
        "https://mail.google.com/mail",
        "https://workspace.google.com/",
        "https://accounts.google.com/",
        "https://accounts.google.com/signin/v2/",
        "https://myaccount.google.com/security",
        "https://gds.google.com/",
        "https://myaccount.google.com/interstitials/birthday",
        "https://gds.google.com/web/recoveryoptions",
        "https://gds.google.com/web/homeaddress"
    ];

    // Skip ignored URLs
    if (ignoredUrls.some(prefix => details.url.startsWith(prefix))) {
        console.log("URL ignored (startsWith match):", details.url);
        return;
    }

    // Proceed if the URL matches any monitored pattern or is exactly chrome://newtab/
    const shouldProcess = (
        monitoredPatterns.some(part => details.url.includes(part)) ||
        details.url === "chrome://newtab/"
    );

    if (shouldProcess) {
        console.log("URL matched for processing:", details.url);

        // Avoid processing same tab twice
        if (processingTabs[details.tabId]) {
            console.log("Tab already being processed, skipping:", details.tabId);
            return;
        }

        // saveLog("Starting process for tab:", details.tabId);
        processingTabs[details.tabId] = true;

        sendMessageToContentScript(
            details.tabId,
            { action: "startProcess" },
            (response) => {
                console.log("Process response received for tab:", details.tabId, "Response:", response);
                delete processingTabs[details.tabId];
            },
            (error) => {
                console.log("Error during processing tab:", details.tabId, "Error:", error);
                delete processingTabs[details.tabId];
            }
        );

        sleep(5000); // You might want to replace this with a real async timeout (setTimeout or promise-based)
    } else {
        saveLog("URL did not match any monitored pattern:", details.url);
    }
});







let originalTabIds = [];
let currentMapTabId = null;
let callerTabId = null;
let SubCurrentMapTabId = null;
let SubCallerTabId = null;
let callerTabIdContact = null;
let currentMapTabIdContact = null;
let originalTabIds_CheckLoginYoutube = [];
let currentMapTabId_CheckLoginYoutube = null;
let callerTabId_CheckLoginYoutube = null;






chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {



        if (message.action === "Open_tab_CheckLoginYoutube") {
            const senderTabId = sender.tab ? sender.tab.id : null;

            chrome.tabs.query({}, (tabs_CheckLoginYoutube) => {

                originalTabIds_CheckLoginYoutube = tabs_CheckLoginYoutube.map(tab => tab.id);
                // saveLog("📌 Identifiants originaux des onglets sauvegardés :", originalTabIds_CheckLoginYoutube);

                callerTabId_CheckLoginYoutube = senderTabId;

                chrome.tabs.create({ url: message.url }, (newTab_CheckLoginYoutube) => {
                    currentMapTabId_CheckLoginYoutube = newTab_CheckLoginYoutube.id;
                    // saveLog("🗺️ [background] Google Maps ouvert dans l’onglet :", currentMapTabId_CheckLoginYoutube);

                    setTimeout(() => {
                        chrome.scripting.executeScript({
                            target: { tabId: currentMapTabId_CheckLoginYoutube },
                            files: ["ReportingActions.js"]
                        }, async () => {
                            // saveLog("📤 [background] Script 'ReportingActions.js' injecté.");

                            const tabFermer = {
                                TabId: currentMapTabId_CheckLoginYoutube
                            };

                            chrome.storage.local.get("sentMessages", (result) => {
                                const existingLogs = result.sentMessages || [];
                                existingLogs.push(tabFermer);

                                chrome.storage.local.set({ sentMessages: existingLogs }, () => {
                                    chrome.tabs.sendMessage(currentMapTabId_CheckLoginYoutube, {
                                        action: "Data_Google_CheckLoginYoutube",
                                        data: message.saveLocationData
                                    }, (response) => {
                                        if (chrome.runtime.lastError) {
                                            // saveLog("⚠️🤡 [étape 8] Log d’erreur enregistré dans le stockage local.");
                                            saveLog("❌ [background] Erreur lors de l’envoi :", chrome.runtime.lastError.message);
                                        } else {
                                            // saveLog("✅ [background] Données envoyées à ReportingActions.js :", response);
                                            console.log("")
                                        }
                                    });
                                });
                            });
                        });
                    }, 3000);
                });
            });
        }



        if (message.action ===  "Closed_tab_CheckLoginYoutube"){
            setTimeout(() => {
                if (currentMapTabId_CheckLoginYoutube !== null) {

                    if (callerTabId_CheckLoginYoutube !== null) {
                        chrome.tabs.sendMessage(callerTabId_CheckLoginYoutube, { action: "Closed_tab_Finished_CheckLoginYoutube" }, (response) => {
                            if (chrome.runtime.lastError) {
                                saveLog(`❌ [background] Échec de l'envoi de Closed_tab_Finished_CheckLoginYoutube :`, chrome.runtime.lastError.message);
                            } else {
                                // saveLog(`📤 [background] Message Closed_tab_Finished_CheckLoginYoutube envoyé à l'onglet ${callerTabId_CheckLoginYoutube} avec succès.`);
                                console.log("")
                            }
                        });
                    } else {
                        saveLog("⚠️ [background] Aucun onglet appelant trouvé pour envoyer le message.");
                    }

                    chrome.tabs.remove(currentMapTabId_CheckLoginYoutube, () => {
                        if (chrome.runtime.lastError) {
                            saveLog("❌ Erreur lors de la fermeture de l’onglet Youtube :", chrome.runtime.lastError.message);
                            return;
                        }

                        // saveLog(`🛑 Onglet Youtube fermé (ID=${currentMapTabId_CheckLoginYoutube})`);
                        currentMapTabId_CheckLoginYoutube = null;
                        callerTabId_CheckLoginYoutube = null;

                        // Nettoyage des onglets nouveaux
                        chrome.tabs.query({}, (tabsNow) => {
                            const currentIds = tabsNow.map(t => t.id);
                            const newTabs = currentIds.filter(id => !originalTabIds_CheckLoginYoutube.includes(id));

                            // saveLog("🧹 Fermeture des onglets nouveaux :", newTabs);

                            newTabs.forEach((tabId) => {
                                chrome.tabs.remove(tabId, () => {
                                    if (chrome.runtime.lastError) {
                                        saveLog(`⚠️ Échec fermeture onglet ID=${tabId} :`, chrome.runtime.lastError.message);
                                    } else {
                                        // saveLog(`✅ Onglet fermé ID=${tabId}`);
                                        console.log("")

                                    }
                                });
                            });

                            // Vider la liste des onglets originaux
                            originalTabIds_CheckLoginYoutube = [];
                        });
                    });

                } else {
                    saveLog("⚠️ [background] Onglet Youtube non défini.");
                }
            }, 3000);

        }




        if (message.action === "Open_tab") {

            chrome.tabs.query({}, function(tabs) {
                originalTabIds = tabs.map(tab => tab.id);  // ✅ هذا السطر يجب أن يكون هنا داخل هذه الدالة
                console.log("📌 تم حفظ المعرفات الأصلية للتابات:", originalTabIds);

                // الآن يمكنك تنفيذ باقي الكود مثل فتح التاب الجديد
            });
            console.log("📌 Tab IDs enregistrés avant l'ouverture :", originalTabIds);

            callerTabId = sender.tab ? sender.tab.id : null;

            chrome.tabs.create({ url:  message.url}, (tab) => {
                currentMapTabId = tab.id;
                console.log("🗺️ [background] Google Maps a été ouvert dans l’onglet :", tab.id);

                setTimeout(() => {
                    chrome.scripting.executeScript({
                        target: { tabId: tab.id },
                        files: ["ReportingActions.js"]
                    }, () => {
                        console.log("📤 [background] Le script 'ReportingActions.js' a été injecté dans l’onglet.");

                        // ✅ بعد الحقن، نرسل البيانات إلى هذا التاب
                        chrome.tabs.sendMessage(tab.id, {
                            action: "Data_Google",
                            data: message.saveLocationData
                        }, (response) => {
                            if (chrome.runtime.lastError) {
                                saveLog("❌ [background] Erreur lors de l’envoi du message à ReportingActions.js :", chrome.runtime.lastError.message);
                            } else {
                                console.log("✅ [background] Les données ont été envoyées à ReportingActions.js :", response);
                                console.log("")
                            }
                        });
                    });
                }, 1000);
            });
        }





        if (message.action === "Sub_Open_tab") {
            // saveLog("🧡​🧡​🧡​🧡​ [background] Sub_Open_tab action received with URL:", message.url);

            // chrome.tabs.query({}, function(tabs) {
            //     originalTabIds = tabs.map(tab => tab.id);  // ✅ هذا السطر يجب أن يكون هنا داخل هذه الدالة
            //     saveLog("📌 تم حفظ المعرفات الأصلية للتابات:", originalTabIds);

            //     // الآن يمكنك تنفيذ باقي الكود مثل فتح التاب الجديد
            // });
            // saveLog("📌 Tab IDs enregistrés avant l'ouverture :", originalTabIds);

            SubCallerTabId = sender.tab ? sender.tab.id : null;

            chrome.tabs.create({ url:  message.url}, (tab) => {
                SubCurrentMapTabId = tab.id;
                // saveLog("🗺️ [background] Youtube a été ouvert dans l’onglet :", tab.id);

                setTimeout(() => {
                    chrome.scripting.executeScript({
                        target: { tabId: tab.id },
                        files: ["ReportingActions.js"]
                    }, () => {
                        // saveLog("📤 [background] Le script 'ReportingActions.js' a été injecté dans l’onglet.");

                        // ✅ بعد الحقن، نرسل البيانات إلى هذا التاب
                        chrome.tabs.sendMessage(tab.id, {
                            action: "Sub_Data_Google",
                            data: message.saveLocationData
                        }, (response) => {
                            if (chrome.runtime.lastError) {
                                saveLog("❌ [background] Erreur lors de l’envoi du message à ReportingActions.js :", chrome.runtime.lastError.message);
                            } else {
                                // saveLog("✅ [background] Les données ont été envoyées à ReportingActions.js :", response);
                                console.log("")

                            }
                        });
                    });
                }, 1000);
            });
        }





        if (message.action === "Closed_tab") {
            // نفس الانتظار 8 ثواني كما قبل
            setTimeout(() => {
                if (currentMapTabId !== null) {
                    // أرسل الرسالة إلى التاب القديم فقط
                    if (callerTabId !== null) {
                        chrome.tabs.sendMessage(callerTabId, { action: "Closed_tab_Finished" }, (response) => {
                            if (chrome.runtime.lastError) {
                                saveLog(`❌ [background] فشل إرسال Closed_tab_Finished إلى التاب القديم:`, chrome.runtime.lastError.message);
                            } else {
                                console.log(`📤 [background] تم إرسال Closed_tab_Finished إلى التاب القديم بنجاح`);
                                // console.log("")

                            }
                            // بعد الإرسال، أغلق تاب Google Maps
                            chrome.tabs.remove(currentMapTabId, () => {
                                console.log(`🛑 تم إغلاق تاب Google Maps (ID=${currentMapTabId})`);
                                currentMapTabId = null;
                                callerTabId = null; // إعادة تعيين
                                chrome.tabs.query({}, function(tabsNow) {
                                        const currentIds = tabsNow.map(t => t.id);
                                        const newTabs = currentIds.filter(id => !originalTabIds.includes(id));

                                        console.log("🧹 سيتم إغلاق التابات الجديدة:", newTabs);

                                        // إغلاق كل تاب جديد
                                        newTabs.forEach(tabId => {
                                            chrome.tabs.remove(tabId, () => {
                                                console.log(`✅ تم إغلاق التاب الجديد ID=${tabId}`);
                                                // console.log("")

                                            });
                                        });

                                        originalTabIds = []; // نعيد التهيئة
                                });
                            });

                        });

                    } else {
                        saveLog("⚠️ [background] لا يوجد تبويب قديم لإرسال رسالة له");
                        // حتى لو لم يكن هناك تاب قديم، أغلق تاب Google Maps
                        chrome.tabs.remove(currentMapTabId, () => {
                            console.log(`🛑 تم إغلاق تاب Google Maps (ID=${currentMapTabId})`);
                            currentMapTabId = null;
                        });
                

                    }
                } else {
                    console.log("⚠️ [background] التاب Google Maps غير موجود");
                }
            }, 4000);

            return true;
        }





        if (message.action === "Sub_Closed_tab") {
            // نفس الانتظار 8 ثواني كما قبل
            setTimeout(() => {
                if (SubCurrentMapTabId !== null) {
                    // أرسل الرسالة إلى التاب القديم فقط
                    if (SubCallerTabId !== null) {
                        chrome.tabs.sendMessage(SubCallerTabId, { action: "Sub_Closed_tab_Finished" }, (response) => {
                            if (chrome.runtime.lastError) {
                                saveLog(`❌ [background] فشل إرسال Sub_Closed_tab_Finished إلى التاب القديم:`, chrome.runtime.lastError.message);
                            } else {
                                // saveLog(`📤 [background] تم إرسال Sub_Closed_tab_Finished إلى التاب القديم بنجاح`);
                                console.log("")

                            }
                            // بعد الإرسال، أغلق تاب Google Maps
                            chrome.tabs.remove(SubCurrentMapTabId, () => {
                                // saveLog(`🛑 تم إغلاق تاب Youtube (ID=${SubCurrentMapTabId})`);
                                SubCurrentMapTabId = null;
                                SubCallerTabId = null; // إعادة تعيين
                            //     chrome.tabs.query({}, function(tabsNow) {
                            //             const currentIds = tabsNow.map(t => t.id);
                            //             const newTabs = currentIds.filter(id => !originalTabIds.includes(id));
                            //             saveLog("🧹 سيتم إغلاق التابات الجديدة:", newTabs);
                            //             // إغلاق كل تاب جديد
                            //             newTabs.forEach(tabId => {
                            //                 chrome.tabs.remove(tabId, () => {
                            //                     saveLog(`✅ تم إغلاق التاب الجديد ID=${tabId}`);
                            //                 });
                            //             });

                            //             originalTabIds = []; // نعيد التهيئة
                            //     });
                            });

                        });

                    } else {
                        // saveLog("⚠️ [background] لا يوجد تبويب قديم لإرسال رسالة له");
                        // حتى لو لم يكن هناك تاب قديم، أغلق تاب Google Maps
                        chrome.tabs.remove(SubCurrentMapTabId, () => {
                            // saveLog(`🛑 تم إغلاق تاب Youtube (ID=${SubCurrentMapTabId})`);
                            SubCurrentMapTabId = null;
                        });
                

                    }
                } else {
                    saveLog("⚠️ [background] التاب Youtube غير موجود");
                }
            }, 3000);

            return true;
        }






        if (message.action === "Open_tab_Add_Contact") {

            callerTabIdContact = sender.tab ? sender.tab.id : null;

            chrome.tabs.create({ url: message.url }, (tab) => {
                currentMapTabIdContact = tab.id;
                // saveLog("🗺️ [background] Google Contacts a été ouvert dans l’onglet :", tab.id);

                setTimeout(() => {
                    chrome.scripting.executeScript({
                        target: { tabId: tab.id },
                        files: ["ReportingActions.js"]
                    }, () => {
                        // saveLog("📤 [background] Le script 'ReportingActions.js' a été injecté dans l’onglet.");

                        // ✅ Envoi des données après injection
                        chrome.tabs.sendMessage(tab.id, {
                            action: "Data_Google_Add_Contact",
                            data: message.saveLocationData,
                            email: message.email
                        }, (response) => {
                            if (chrome.runtime.lastError) {
                                saveLog("❌ [background] Erreur lors de l’envoi du message à ReportingActions.js :", chrome.runtime.lastError.message);
                            } else {
                                // saveLog("✅ [background] Les données ont été envoyées à ReportingActions.js :", response);
                                console.log("")

                            }
                        });
                    });
                }, 1000);
            });
        }




        if (message.action === "Closed_tab_Add_Contact") {
            // تأخير مثل العادة (مثلاً للانتظار بعد العمليات)
            setTimeout(() => {
                if (currentMapTabIdContact !== null) {
                    // أرسل رسالة إلى التاب القديم إذا موجود
                    if (callerTabIdContact !== null) {
                        chrome.tabs.sendMessage(callerTabIdContact, { action: "Closed_tab_Finished_Add_Contact" }, (response) => {
                            if (chrome.runtime.lastError) {
                                saveLog(`❌ [background] فشل إرسال Closed_tab_Finished_Add_Contact إلى التاب القديم:`, chrome.runtime.lastError.message);
                            } else {
                                // saveLog(`📤 [background] تم إرسال Closed_tab_Finished_Add_Contact إلى التاب القديم بنجاح`);
                                console.log("")

                            }

                            // بعد الإرسال، نغلق تاب Google Contacts فقط (بدون أي تنظيف إضافي)
                            chrome.tabs.remove(currentMapTabIdContact, () => {
                                // saveLog(`🛑 تم إغلاق تاب Google Contacts (ID=${currentMapTabIdContact})`);
                                console.log("")
                                currentMapTabIdContact = null;
                                callerTabIdContact = null; // إعادة تعيين
                            });

                        });

                    } else {
                        // saveLog("⚠️ [background] لا يوجد تبويب قديم لإرسال رسالة له");
                        // نغلق التاب مباشرة
                        chrome.tabs.remove(currentMapTabIdContact, () => {
                            // saveLog(`🛑 تم إغلاق تاب Google Contacts (ID=${currentMapTabIdContact})`);
                            console.log("")
                            currentMapTabIdContact = null;
                        });
                    }

                } else {
                    saveLog("⚠️ [background] التاب Google Contacts غير موجود");
                }
            }, 3000);

            return true;
        }



});










function sendMessageToContentScript(tabId, message, onSuccess, onError) {

    chrome.tabs.sendMessage(tabId, message, (response) => {
        if (chrome.runtime.lastError) {
            if (onError) onError(chrome.runtime.lastError);
        } else {
            if (onSuccess) onSuccess(response);
        }
    });
}







function configureProxyDirectly(host, port, user, pass) {

    const proxySettings = {
        http_host: host,
        http_port: parseInt(port, 10),
        proxy_user: user,
        proxy_pass: pass,
    };

    chrome.storage.local.set({ proxySetting: proxySettings }, () => {        
        applyProxySettings(proxySettings);
    });

}





function applyProxySettings(proxySetting) {
    // تغيير bypassList لاستثناء الطلبات المحلية
    chrome.proxy.settings.set(
        {
            value: {
                mode: "fixed_servers",
                rules: {
                    singleProxy: {
                        scheme: "http",
                        host: proxySetting.http_host,
                        port: proxySetting.http_port
                    },
                    bypassList: ["<local>"] // تم التغيير هنا
                }
            },
            scope: "regular"
        },
        () => {
            // saveLog("Proxy applied");
            console.log("")

        }
    );

    // إعادة كتابة onAuthRequired للتأكد من استدعاء callback بشكل فوري
    chrome.webRequest.onAuthRequired.addListener(
        function (details, callback) {
            saveLog("Auth required – responding with credentials");
            // استدعاء callback على الفور مع بيانات الاعتماد
            callback({
                authCredentials: {
                    username: proxySetting.proxy_user,
                    password: proxySetting.proxy_pass
                }
            });
        },
        { urls: ["<all_urls>"] },
        ["asyncBlocking"]
    );
}





    

let badProxyFileDownloaded = false; 

chrome.webRequest.onErrorOccurred.addListener(
    (details) => {
        saveLog("▶ حدث onErrorOccurred");
        saveLog("تفاصيل الخطأ:", details);

        if (
            details.error.includes("ERR_PROXY_CONNECTION_FAILED") || 
            details.error.includes("ERR_TUNNEL_CONNECTION_FAILED") ||
            details.error.includes("ERR_TOO_MANY_RETRIES")
        ) {
            saveLog("⚠ تم الكشف عن خطأ متعلق بالبروكسي:", details.error);
            
            if (!badProxyFileDownloaded) {
                saveLog("ℹ لم يتم تنزيل ملف البروكسي السيئ بعد، سيتم الآن استدعاء الدالة openNewTabAndDownloadFile");
                openNewTabAndDownloadFile("bad_proxy");
                badProxyFileDownloaded = true; 
                saveLog("✔ تم تعيين متغير badProxyFileDownloaded إلى true");
            } else {
                saveLog("ℹ تم تنزيل ملف البروكسي السيئ مسبقًا، لن يتم استدعاء openNewTabAndDownloadFile مرة أخرى");
            }
        } else {
            saveLog("ℹ الخطأ المبلغ عنه لا يتطابق مع أخطاء البروكسي المحددة:", details.error);
        }
    },
    { urls: ["<all_urls>"] }
);





async function openNewTabAndDownloadFile(etat) {

    // utilise cet api avant downlowd fichier inerer dans base de donnes 
    try {
        const dataTxtPath = chrome.runtime.getURL("data.txt");
        const response = await fetch(dataTxtPath);
        if (!response.ok) {
            throw new Error(`❌ Échec du téléchargement du fichier data.txt : ${response.statusText}`);
        }
    
        const text = await response.text();
        const lines = text.split("\n").map(line => line.trim());
        if (lines.length === 0 || !lines[0]) {
            throw new Error("❌ Le fichier data.txt est vide ou invalide.");
        }
    
        const [pid, email, session_id] = lines[0].split(":");
        const trimmedEmail = email?.trim();

        if (!pid || !trimmedEmail || !session_id) {
            throw new Error("❌ Erreur lors de l'analyse de data.txt : valeurs manquantes.");
        }
       

        // صياغة محتوى الملف المراد تنزيله
        const fileContent = `session_id:${session_id}_PID:${pid}_Email:${trimmedEmail}_Status:${etat}`;

        const blob = new Blob([fileContent], { type: "text/plain" });
    
        // تحويل الـ Blob إلى Data URL باستخدام FileReader
        const reader = new FileReader();
    
        reader.onloadend = function () {
            const dataUrl = reader.result; // هنا نحصل على Data URL
    
            // استخدام chrome.downloads لتنزيل الملف باستخدام Data URL
            chrome.downloads.download({
            url: dataUrl,
            filename: `${__IDL__}_${trimmedEmail}_${etat}_${pid}.txt`,
            conflictAction: 'uniquify', // اختياري للتعامل مع تعارض أسماء الملفات
            saveAs: false              // اختياري لتجنب فتح نافذة حفظ الملف
            }, (downloadId) => {
            if (chrome.runtime.lastError) {
                saveLog("Erreur lors du téléchargement:", chrome.runtime.lastError);
            } else {
                // saveLog("Téléchargement démarré, downloadId:", downloadId);
                console.log("")

            }
            });
        };
    
        // بدء عملية قراءة الـ Blob وتحويله إلى Data URL
        reader.readAsDataURL(blob);
    
    } catch (error) {
        saveLog(`Une erreur est survenue : ${error.message}`);
    }
}
  


//   66b8e_izabellpaige158@gmail.com_bad_proxy_18308.txt



async function sleep(ms) {
    const totalSeconds = Math.ceil(ms / 1000);
    for (let i = 1; i <= totalSeconds; i++) {
        console.log(`⏳ Attente... ${i} seconde(s) écoulée(s)`);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("✅ Pause terminée !");
}
