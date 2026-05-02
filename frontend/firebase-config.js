// frontend/firebase-config.js
const firebaseConfig = {
  apiKey: "",
  authDomain: "",
  databaseURL: "",
  projectId: "",
  storageBucket: "",
  messagingSenderId: "",
  appId: ""
};

// Initialize Firebase using the Compat (Compatibility) SDK
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

// Initialize Services
const db = firebase.database();
const auth = firebase.auth();

console.log("🚀 RaktaSetu Cloud Node: Connected to Asia-Southeast1");