import Chessboard from "./components/Chessboard";
import {Color} from "./gameLogic"
const hi = Color.BLACK
function App() {
  return (
    <main>
      <h1>Chessboard</h1>
      <h1>{Color.other(hi)}</h1>
      <Chessboard/>
    </main>
  );
}

export default App;
