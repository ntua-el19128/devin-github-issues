export default function Button({ children, onClick, variant = "btn", ...rest }) {
  return (
    <button className={`btn ${variant}`} onClick={onClick} {...rest}>
      {children}
    </button>
  );
}