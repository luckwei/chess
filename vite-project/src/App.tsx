import Chessboard from "./components/Chessboard";
import { CastlingPermission, Color, Flag, Move } from "./gameLogic";

class UM extends Map {
  
  set(key: [Color, Flag], value: any) {
    return super.set(key.toString(), value);
  }

  get(key: [Color, Flag]){
    return super.get(key.toString());
  }
  has(key: [Color, Flag]) {
    return super.has(key.toString())
  }
  
}

let m = new Map()
m.set(Color.WHITE, true)

function App() {
  return (
    <main>
      <h1>Chessboard</h1>
      <h1>{m.has(Color.WHITE)? "something":"there is nothing"}</h1>
      <Chessboard />
    </main>
  );
}

export default App;
