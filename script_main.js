window.onload = function () {
    const country = document.querySelector('select[name="iso2"]');
    const city = document.querySelector('select[name="city"]');
    city.disabled = true;

    function updateCityOptions(countryN) {
        city.innerHTML = '<option>Loading cities...</option>';
        city.disabled = true;

        fetch('https://countriesnow.space/api/v0.1/countries/cities', {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({country: countryN})
        })
            .then(response => response.json())
            .then(data => {
            city.innerHTML = '';
            if (data.data && data.data.length > 0) {
                data.data.forEach(cityName => {
                    const option = document.createElement('option');
                    option.value = cityName;
                    option.textContent = cityName;
                    city.appendChild(option)
                });
                city.disabled = false;
            } else {
                city.innerHTML = '<option>No cities found</option>';
                city.disabled = false;
            }

    })
            .catch(error => {
            console.error("Error fetching cities:", error);
            city.innerHTML = '<option>Error loading cities</option>'
            city.disabled = true;
    });
}
country.addEventListener('change', function () {
    const selectedOpt = this.options[this.selectedIndex];
    const countryN = selectedOpt.textContent;
    if (countryN) {
        updateCityOptions(countryN)
    }
})}