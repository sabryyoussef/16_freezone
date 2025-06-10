window.addEventListener('load', e => {
  registerSW();
});

async function registerSW() {
  if ('serviceWorker' in navigator) {

    navigator.serviceWorker.register("/ks_curved_backend_theme_enter/get/sw.js", { scope: "/web/" }).then(function(registration) {
      // Registration was successful
      console.log('ServiceWorker registration successful with scope: ', registration.scope);
    }, function(err) {
      // registration failed :(
      console.log('ServiceWorker registration failed: ', err);
    });
  }
}