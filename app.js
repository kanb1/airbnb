// 
function test(items){
    // console.log(items)
    items = JSON.parse(items)
    console.log(items)
    items.forEach( item => {
        let marker = new mapboxgl.Marker()
        .setLngLat([item.item_lon, item.item_lat]) // Marker 1 coordinates
        .addTo(map);        
    })
}


    function showNextImage(itemPk) {
        const imageElement = document.getElementById(`image-${itemPk}`);
        const images = JSON.parse(imageElement.dataset.images);
        let currentIndex = parseInt(imageElement.dataset.index, 10);

        currentIndex = (currentIndex + 1) % images.length;
        imageElement.src = `/images/${images[currentIndex]}`;
        imageElement.dataset.index = currentIndex;
    }
