import React from "react";
import { Book } from "../types/book";
import BookCard from "./BookCard";

type BookListProps = {
  books: Book[];
  onSelectBook: (id: string) => void;
};

const BookList = ({ books, onSelectBook }: BookListProps) => {
  return (
    <div>
      {books.map((book) => (
        <BookCard
          key={book.id}
          book={book}
          onClick={() => onSelectBook(book.id)}
        />
      ))}
    </div>
  );
};

export default BookList;
