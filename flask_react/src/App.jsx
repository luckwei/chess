import axios from "axios";
import { useState } from "react";
import "./App.css";

function App() {
  const [profileData, setProfileData] = useState(null);

  function getData() {
    // console.log("Hello")
    axios({
      method: "GET",
      url: "/api/profile",
    })
      .then((response) => {
        const res = response.data;
        setProfileData({
          data: res.data,
        });
      })
      .catch((error) => {
        if (error.response) {
          console.log(error.response);
          console.log(error.response.status);
          console.log(error.response.headers);
        }
      });
  }

  return (
    <div className="App">
      <header className="App-header">
        <p>To get your profile details: </p>
        <button onClick={getData}>Click me</button>
        {profileData && (
          <div>
            <p>Profile name: {JSON.stringify(profileData)}</p>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
