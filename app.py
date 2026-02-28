import streamlit as st

st.title('Coil Optimizer')

# Input parameters
inner_diameter = st.number_input('Inner Diameter (mm)', min_value=0.0)
outer_diameter = st.number_input('Outer Diameter (mm)', min_value=0.0)
coil_length = st.number_input('Coil Length (mm)', min_value=0.0)

# Calculate coil parameters
if st.button('Optimize'):
    if outer_diameter <= inner_diameter:
        st.error('Outer diameter must be greater than inner diameter.')
    else:
        optimized_value = (outer_diameter - inner_diameter) / coil_length  # Placeholder calculation
        st.success(f'Optimized Value: {optimized_value}')
