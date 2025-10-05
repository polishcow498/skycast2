window.onload = function () {
    const countrySelect = document.querySelector('select[name="iso2"]');
    const citySelect = document.querySelector('select[name="city"]');
    citySelcityect.disabled = true;

    function updateCityOptions(countryName) {
        citySelect.innerHTML = `<option>Loading...</option>`;
        citySelect.disabled = true;

        fetch('https://countriesnow.space/api/v0.1/countries/cities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ country: countryName })
        })
        .then(response => response.json())
        .then(data => {
            citySelect.innerHTML = '';

            if (data.data && data.data.length > 0) {
                data.data.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    citySelect.appendChild(option);
                });
                citySelect.disabled = false;
            } else {
                citySelect.innerHTML = `<option>No cities found</option>`;
                citySelect.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error fetching cities:', error);
            citySelect.innerHTML = `<option>Error loading cities</option>`;
            citySelect.disabled = true;
        });
    }

    countrySelect.addEventListener('change', function () {
        const selectedOption = this.options[this.selectedIndex];
        const countryName = selectedOption.textContent;
        if (countryName) {
            updateCityOptions(countryName);
        }
    });
};