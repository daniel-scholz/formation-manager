window.onload = function () {
    document.cookie =
        document.addEventListener("DOMContentLoaded", function (e) {
            console.log("ready!")
            league_options = document.getElementsByClassName("league_option")
            for (let elem of league_options) {
                elem.addEventListener("click", function (e) {
                    hidden_field = document.createElement("input")
                    hidden_field.setAttribute("hidden", "")
                    hidden_field.setAttribute("name", "league_id")
                    hidden_field.setAttribute("value", e.target.id.split("_")[1])
                    auth_cookie = document.createElement("input")
                    auth_cookie.setAttribute("hidden", "")
                    auth_cookie.setAttribute("name", "auth_token")
                    auth_cookie.setAttribute("value", getCookieValue("auth_token"))
                    elem.appendChild(hidden_field)
                    elem.appendChild(auth_cookie)
                    console.log(hidden_field)
                    console.log(auth_cookie)

                    document.getElementById("choose_form").submit()
                })
            }
        });

    function getCookieValue(a) {
        var b = document.cookie.match('(^|;)\\s*' + a + '\\s*=\\s*([^;]+)');
        return b ? b.pop() : '';
    }
}()