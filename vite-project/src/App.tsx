import Tile from "./components/Tile";

function App() {
  return (
    <main>
      <h1>Hello World</h1>
      <div className="chessboard">{Array(64).fill(<Tile />)}</div>
    </main>
  );
}

export default App;
