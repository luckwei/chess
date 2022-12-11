import axios from "axios";
import { useState } from "react";
import "./App.css";

const chessPieces = {
  black: {
    pawn: "♙",
    rook: "♖",
    knight: "♘",
    bishop: "♗",
    queen: "♕",
    king: "♔",
  },
  white: {
    pawn: "♟",
    rook: "♜",
    knight: "♞",
    bishop: "♝",
    queen: "♕",
    king: "♚",
  },
  none: { none: " " },
};

function App() {
  const [chessData, setChessData] = useState(null);

  function getBoard() {
    // console.log("Hello")
    axios({
      method: "GET",
      url: "/api/board",
    })
      .then((response) => {
        const { updates, available_moves } = response.data;
        let updatesPiece = Object.fromEntries(
          Object.entries(updates).map(([key, value]) => {
            const { color, type } = value;

            return [key, chessPieces[color][type]];
          })
        );

        console.log();
        setChessData({
          updates: updatesPiece,
          available_moves: available_moves,
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

  function chooseMove() {}

  function newRandomGame() {}

  return (
    <div className="App">
      <header className="App-header">
        <p>Chess API test: </p>
        <button onClick={getBoard}>Click me</button>
        {chessData && (
          <div>
            <p>updates: {JSON.stringify(chessData.updates)}</p>
            <p>available_moves: {JSON.stringify(chessData.available_moves)}</p>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
