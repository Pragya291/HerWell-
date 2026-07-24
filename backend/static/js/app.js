fetch('/api/health')
  .then(res => res.json())
  .then(data => {
    document.getElementById('app-content').innerHTML = <h2></h2>;
  })
  .catch(err => {
    document.getElementById('app-content').innerHTML = '<p>Error connecting to API</p>';
  });
