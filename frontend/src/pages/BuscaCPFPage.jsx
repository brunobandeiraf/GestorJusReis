import BuscaCPF from '../components/BuscaCPF/index';

function BuscaCPFPage() {
  return (
    <div style={styles.container}>
      <BuscaCPF />
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '1rem',
  },
};

export default BuscaCPFPage;
