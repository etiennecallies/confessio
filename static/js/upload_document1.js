// Register plugins
FilePond.registerPlugin(FilePondPluginFileValidateType);
FilePond.registerPlugin(FilePondPluginImagePreview);

// Turn all file input elements into ponds
const pond = FilePond.create(document.querySelector('.filepond'), {
    allowMultiple: false,
    instantUpload: false,
    storeAsFile: true,
    required: true,
    acceptedFileTypes: ['image/*'],
    labelFileTypeNotAllowed: 'Seules les images au format .png, .jpg, .jpeg ou .webp sont acceptées.',
    // captureMethod: 'environment', // Is actually skipping the gallery
    credits: ['', ''],
    dropOnPage: true,
    labelIdle: 'Déposer une image ou <span class="filepond--label-action browse-picture">Parcourir</span> ou <span class="filepond--label-action take-picture">Prendre une photo</span>',
});

// Wait for FilePond to be ready, then add our custom listeners
pond.on('initfile', () => {
    setupCustomListeners();
});

// Optional: Re-setup listeners when FilePond updates its DOM
pond.on('updatefiles', () => {
    // Small delay to ensure DOM is updated
    setTimeout(setupCustomListeners, 50);
});

// Also setup listeners immediately in case the pond is already ready
setTimeout(setupCustomListeners, 100);

function setupCustomListeners() {
    const pondElement = pond.element;

    // Find the browse and take picture spans
    const browseSpan = pondElement.querySelector('.browse-picture');
    const takeSpan = pondElement.querySelector('.take-picture');

    if (browseSpan && takeSpan) {
        // Add click listeners to our custom spans
        $(browseSpan).off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // Set capture to null for gallery browsing
            pond.setOptions({
                captureMethod: null
            });

            // Use FilePond's built-in browse method
            pond.browse();
        });

        $(takeSpan).off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // Set capture to environment for camera
            pond.setOptions({
                captureMethod: 'environment'
            });

            // Use FilePond's built-in browse method
            pond.browse();
        });
    }
}
