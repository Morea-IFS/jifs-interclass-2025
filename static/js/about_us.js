const menuMobileManagment = () => {
    const burguer = document.querySelector('.icon-burguer');
    const nav = document.querySelector('header nav ul');
    const elementsMobile = document.querySelectorAll('.mobile')
    const close = document.querySelector('.icon-close');

    const onBurguerClick = () => {
        nav.style.display = 'flex';
        elementsMobile.forEach((item) => {
            item.style.display = 'flex';
        })
    };

    const onCloseClick = () => {
        nav.style.display = 'none';
        elementsMobile.forEach((item) => {
            item.style.display = 'none';
        })
    };

    burguer.addEventListener('click', onBurguerClick);
    close.addEventListener('click', onCloseClick);
}
menuMobileManagment();