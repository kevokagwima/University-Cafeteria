const user = document.querySelector("#login");
const login = document.querySelector(".login");

user.addEventListener("click", () => {
  login.classList.toggle("show-login");
});
