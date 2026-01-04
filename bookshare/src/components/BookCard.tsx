import { Book } from "../types/book";

type BookCardProps = {
  book: Book;
  onClick: () => void;
};

const BookCard = ({ book, onClick }: BookCardProps) => {
  return (
    <div onClick={onClick} style={{ cursor: "pointer" }}>
      <img src={book.imageUrl} alt={book.title} width={100} height={100} />
      <div>
        <h3>{book.title}</h3>
        <p>{book.reviews.length}人が読みました</p>
      </div>
    </div>
  );
};

export default BookCard;
