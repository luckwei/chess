import Tile from "./Tile";

function Chessboard() {
  return <div className="chessboard">{Array(64).fill(<Tile />)}</div>;
}

export default Chessboard;
